import datetime
import ipdb
import re
from decimal import Decimal

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from powerdispatcher.conf import settings
from powerdispatcher.models import ProjectConfiguration
from powerdispatcher.scraper.base_mixing import ScraperBaseMixin
from powerdispatcher.utils import get_datetime_obj_from_str, trunc_date


class PowerdispatchSiteScraper(ScraperBaseMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        project_configuration = ProjectConfiguration.objects.get()
        self.current_account = {
            "account": project_configuration.powerdispatch_account,
            "username": project_configuration.powerdispatch_username,
            "password": project_configuration.powerdispatch_password,
        }
        self.account_identifier = "powerdispatch"
        self.webdriver_container_host = "docker-host"
        self.webdriver_container_port = None
        self.blocked_domains = []

    def get_default_options(self):
        options_headers = ["--disable-notifications", "--no-sandbox"]
        initialize_options = {
            "chrome": webdriver.ChromeOptions,
            "firefox": webdriver.FirefoxOptions,
        }
        options_headers += ["--headless"] if settings.HEADLESS else []
        OptionClass = initialize_options.get(self.browser_type)
        options = OptionClass()

        options.add_argument("--start-maximized")
        # options.add_argument("enable-automation")
        # options.add_argument("--disable-extensions")
        # options.add_argument("--dns-prefetch-disable")
        options.add_argument("--disable-gpu")

        for options_header in options_headers:
            options.add_argument(options_header)

        return options

    def get_chrome_options(self, options):

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-geolocation")

        # options.add_argument(f'--user-data-dir=/home/seluser/.config/google-chrome/{user_data_dir_name}')

        prefs = dict()

        # disable geolocation
        prefs["profile.default_content_setting_values.geolocation"] = 2

        # disable "save password?" prompt
        prefs["credentials_enable_service"] = False
        prefs["profile.password_manager_enabled"] = False

        # disable webRTC to avoid real-IP leak
        prefs["webrtc.ip_handling_policy"] = "disable_non_proxied_udp"
        prefs["webrtc.multiple_routes_enabled"] = False
        prefs["webrtc.nonproxied_udp_enabled"] = False

        # Change Language to English (Does not work for XPATH)
        # prefs['translate_whitelists'] = {'uk': 'en'}
        # prefs['translate'] = {'enabled': 'true'}

        options.add_experimental_option("prefs", prefs)

        # some assets are not worth loading and/or take too much time to load
        if len(self.blocked_domains) > 0:
            host_resolver_rules = ", ".join(
                [f"MAP {d} 127.0.0.1" for d in self.blocked_domains]
            )
            options.add_argument(f"--host-resolver-rules={host_resolver_rules}")

        return options

    def get_firefox_options(self, options):
        return options

    def get_options(self):
        options = self.get_default_options()

        if self.browser_type == self.BROWSER_CHROME:
            self.get_chrome_options(options)
        elif self.browser_type == self.BROWSER_FIREFOX:
            self.get_firefox_options(options)
        else:
            raise Exception(f"Browser not supported: {self.browser_type}")

        return options

    def get_driver(self, options):
        initialize_driver = {
            "remote+firefox": webdriver.Remote,
            "remote+chrome": webdriver.Remote,
            "local+chrome": webdriver.Chrome,
        }
        eligible_capabilities = {
            "chrome": DesiredCapabilities.CHROME,
            "firefox": DesiredCapabilities.FIREFOX,
        }
        connection_options = {
            "local": settings.WEB_DRIVER_PATH,
            "remote": self.webdriver_url,
        }

        primary_identifier = f"{settings.CONNECTION_TYPE}+{self.browser_type}"

        DriverClass = initialize_driver[primary_identifier]

        desired_capabilities = eligible_capabilities[self.browser_type]

        # desired_capabilities["pageLoadStrategy"] = "none"

        return DriverClass(
            connection_options[settings.CONNECTION_TYPE],
            desired_capabilities=desired_capabilities,
            options=options,
        )

    def init_driver(self):
        self.options = self.get_options()
        self.log(f"init_driver on {self.webdriver_url}")
        self.driver = self.get_driver(options=self.options)

    def login(self):
        self.navigate_to(settings.POWERDISPATCHER_POWER_DISPATCH_BASE_URL)

        account = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.NAME, "_account"))
        )
        account.send_keys(self.current_account["account"])
        username = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.NAME, "_username"))
        )
        username.send_keys(self.current_account["username"])
        password = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.NAME, "_password"))
        )
        password.send_keys(self.current_account["password"])
        submit = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.NAME, "_submit"))
        )
        submit.click()
        self.sleep(2)
        self.close_twilio_advertise()

    def close_twilio_advertise(self):
        try:
            target_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(text(), ' I acknowledge this notice')]",
                    )
                ),
                message="Close btn not found!",
            )
            target_btn.click()
        except Exception:
            return

    def goto_search_menu(self):
        search_menu_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Search')]")),
            message="Search menu btn not found!",
        )
        search_menu_btn.click()
        self.sleep(2)

    def _filter_search(self, input_date, table_identifier):
        input_date_btn = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, f"{table_identifier}"))
        )
        input_date_btn.click()

        table_root = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, f"{table_identifier}_root"))
        )

        MAX_CLICKS = 5 * 12  # 5 years
        clicks_performed = 0
        while clicks_performed <= MAX_CLICKS:

            table_header = table_root.find_element(
                By.XPATH, "./descendant::div[@class='picker__header']"
            )

            table_month = table_header.find_element(
                By.XPATH, "./div[@class='picker__month']"
            )
            table_year = table_header.find_element(
                By.XPATH, "./div[@class='picker__year']"
            )
            prev_month_btn = table_header.find_element(
                By.XPATH, "./div[@class='picker__nav--prev']"
            )
            next_month_btn = table_header.find_element(
                By.XPATH, "./div[@class='picker__nav--next']"
            )

            DUMMY_DAY = 1

            currently_selected_date_str = (
                f"{DUMMY_DAY} {table_month.text} {table_year.text}"
            )
            currently_selected_date_obj = datetime.datetime.strptime(
                currently_selected_date_str, "%d %B %Y"
            ).date()

            first_day_of_currently_selected = trunc_date(currently_selected_date_obj)
            first_day_of_input_date = trunc_date(input_date)

            if first_day_of_currently_selected > first_day_of_input_date:
                prev_month_btn.click()
            elif first_day_of_currently_selected < first_day_of_input_date:
                next_month_btn.click()
            else:
                break
            clicks_performed += 1

        table_body = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, f"{table_identifier}_table"))
        )

        input_date_str = input_date.strftime("%Y-%m-%d")

        target_day = table_body.find_element(
            By.XPATH, f"./tbody/descendant::div[@aria-label='{input_date_str}']"
        )

        self.sleep(2)

        target_day.click()

    def _filter_status(self, status):
        status_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "ddStatus"))
        )
        status_element_selector = Select(status_element)
        status_element_selector.select_by_value(status)

    def filter_search(self, start_date=None, end_date=None, status=None):
        if start_date:
            self._filter_search(start_date, "txtDate1")
        if end_date:
            self._filter_search(end_date, "txtDate2")
        if status:
            self._filter_status(status)
        submit_btn = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "btnSubmit"))
        )
        self.scroll_to_element(submit_btn)
        submit_btn.click()

    def filter_job_list(self, date):
        self.navigate_to("https://lite.serviceslogin.com/appointments.php?init=1")

        filter_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(text(), 'Filter')]")
            )
        )
        filter_element.click()

        date_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "ddTimeRange"))
        )
        date_element_selector = Select(date_element)
        date_element_selector.select_by_value(date)

        btn_search = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "btnSearch"))
        )
        self.scroll_to_element(btn_search)
        # btn_search.click()
        self.click_element(btn_search)
        self.sleep(10)

    def get_ticket_ids_from_search_result(self, max_results=None):
        MAX_PAGES = 1000  # TODO THIS SHOULD BE ADDED AS A CONFIG PARAMETER
        current_page = 1
        all_ticket_ids = []
        while current_page <= MAX_PAGES:
            try:
                search_result_table = WebDriverWait(self.driver, timeout=20).until(
                    EC.presence_of_element_located((By.ID, "search-result-table"))
                )
            except Exception:
                return all_ticket_ids
            current_page_jobs = search_result_table.find_elements(
                By.XPATH, "./tbody[2]/tr"
            )
            current_page_jobs = search_result_table.find_elements(
                By.XPATH, "./tbody[2]/tr"
            )

            for job in current_page_jobs:
                ticket_id_element = job.find_element(By.XPATH, "./td[5]")
                ticket_id = ticket_id_element.text
                all_ticket_ids.append(ticket_id)
                try:
                    self.scroll_to_element(ticket_id_element)
                except Exception:
                    pass
                if max_results and len(all_ticket_ids) >= max_results:
                    break

            if max_results and len(all_ticket_ids) >= max_results:
                break

            try:
                next_page_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Next')]")
                    ),
                    message="Next page btn not found!",
                )
                next_page_btn.click()
                self.sleep(2)
                current_page += 1
            # except TimeOut
            except Exception:
                break
        if current_page == MAX_PAGES:
            self.log("MAX PAGE UPPER LIMIT FOUND!")
        self.log(f"Found {len(all_ticket_ids)} ticket/s")
        return all_ticket_ids

    def update_ticket_status(self, ticket_id, status):
        ticket_permalink = settings.POWERDISPATCHER_TICKET_URL.format(
            ticket_id=ticket_id
        )
        self.navigate_to(ticket_permalink)
        status_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "ddStatus"))
        )
        status_element_selector = Select(status_element)
        status_element_selector.select_by_value(status)

        if status == "CANCELED":
            self.update_canceled_fields(who_canceled="OFFICE", why_canceled="FU")

        save_btn = WebDriverWait(self.driver, timeout=20).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '//div[@id="paneDocuments"]/following-sibling::button[contains(text(), "Save Job")]',
                )
            )
        )
        ActionChains(self.driver).move_to_element(save_btn).perform()
        save_btn.click()
        WebDriverWait(self.driver, timeout=20).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//a[contains(text(), " Jobs List")]')
            )
        )

    def get_ticket_technician(self):
        technician = (
            WebDriverWait(self.driver, timeout=20)
            .until(EC.presence_of_element_located((By.ID, "select2-ddTech-container")))
            .text
        )
        if "select a technician" in technician.lower():
            technician = None
        return technician

    def get_ticket_status(self):
        status_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "ddStatus"))
        )
        status_selector = Select(status_element)
        status = status_selector.first_selected_option.text
        if status == "Canceled":
            who_canceled_element = WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='cancel_slide']/fieldset/select")
                )
            )
            who_canceled_element_selector = Select(who_canceled_element)

            try:
                selected_option = (
                    who_canceled_element_selector.first_selected_option.text
                )
                who_canceled_str = selected_option if selected_option else None
            except Exception:
                who_canceled_str = None

            why_canceled_element = WebDriverWait(self.driver, timeout=20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='cancel_slide']/fieldset/input")
                )
            )
            why_canceled_str = why_canceled_element.get_attribute("value")
            why_canceled_str = why_canceled_str if why_canceled_str else None
        else:
            who_canceled_str = None
            why_canceled_str = None

        return status, who_canceled_str, why_canceled_str

    def update_canceled_fields(self, who_canceled, why_canceled):
        who_canceled_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='cancel_slide']/descendant::select")
            )
        )
        who_canceled_element_selector = Select(who_canceled_element)
        who_canceled_element_selector.select_by_value(who_canceled)

        why_canceled_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='cancel_slide']/descendant::input")
            )
        )
        why_canceled_element.send_keys(why_canceled)

    def get_ticket_follow_up_info(self):
        alternative_technician = None
        follow_up_given_by_alternative_technician = None
        follow_up_strategy_successfull = None
        comments_child_datetime_elements = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//*[@id='paneComments']/table[2]/tbody/tr/td[2]/*[@class='comment']/descendant::div[@class='header']/span[1]",
                )
            )
        )
        for comments_child_datetime_element in comments_child_datetime_elements:
            self.click_element(comments_child_datetime_element)

        results_found_in_table_dict = {
            "technician": {"table_number": None, "value": None},
            "alternative_technician": {"table_number": None, "value": None},
            "in_progress_final_status": [],
        }
        # Tabla de comentarios en orden
        changelog_elements = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//*[@id='paneComments']/table[2]/tbody/tr/td[2]/*[@class='comment']/descendant::caption[contains(text(), 'Changelog for')]",
                )
            )
        )
        for idx, changelog_element in enumerate(changelog_elements):
            # This is comment since i dont know if in progress status is in call or ticket
            # changelog_table = changelog_element.find_element(By.XPATH, "./parent::table")
            # if "changelog for job" in changelog_element.text.lower():
            #     # job_table
            #     pass
            # elif "changelog for call" in changelog_element.text.lower():
            #     # call table
            #     pass
            if "changelog for job" not in changelog_element.text.lower():
                continue
            job_changelog = changelog_element.find_element(By.XPATH, "./parent::table")
            try:
                found_technician = job_changelog.find_element(
                    By.XPATH,
                    "./descendant::tr/td[text()='technician']/following-sibling::td[2]",
                ).text
                type_of_technician = (
                    "alternative_technician"
                    if "report" in found_technician.lower()
                    else "technician"
                )
                if not results_found_in_table_dict[type_of_technician]["value"]:
                    results_found_in_table_dict[type_of_technician]["table_number"] = (
                        idx + 1
                    )
                    results_found_in_table_dict[type_of_technician][
                        "value"
                    ] = found_technician
            except Exception:
                pass
            try:
                final_status = job_changelog.find_element(
                    By.XPATH,
                    "./descendant::tr/td[text()='status']/following-sibling::td[2]",
                ).text
                if final_status == "INPROGRESS":
                    results_found_in_table_dict["in_progress_final_status"].append(
                        {"table_number": (idx + 1)}
                    )
            except Exception:
                pass

        # Algorithm to decide follow up
        if results_found_in_table_dict["alternative_technician"]["value"]:
            # Hay un tecnico que se llama reports pero no tiene llamada posterior que diga in progress
            alternative_technician = results_found_in_table_dict[
                "alternative_technician"
            ]["value"]
            follow_up_given_by_alternative_technician = False
            follow_up_strategy_successfull = False

        for call_dict in results_found_in_table_dict["in_progress_final_status"]:
            if (
                alternative_technician
                and results_found_in_table_dict["alternative_technician"][
                    "table_number"
                ]
                > call_dict["table_number"]
            ) and (
                not results_found_in_table_dict["technician"]["table_number"]
                or (
                    results_found_in_table_dict["technician"]["table_number"]
                    and call_dict["table_number"]
                    > results_found_in_table_dict["technician"]["table_number"]
                )
            ):
                # Hay un tecnico que se llama reports y tiene llamada posterior que diga in progress
                follow_up_given_by_alternative_technician = True
                break

        if (
            alternative_technician
            and follow_up_given_by_alternative_technician
            and results_found_in_table_dict["technician"]["table_number"]
            and results_found_in_table_dict["alternative_technician"]["table_number"]
            > results_found_in_table_dict["technician"]["table_number"]
        ):
            # Hay un tecnico que se llama reports y tiene llamada posterior que diga in progress y hay un tecnico diferente a reports que fue asignado posteriormente
            follow_up_strategy_successfull = True

        return (
            alternative_technician,
            follow_up_given_by_alternative_technician,
            follow_up_strategy_successfull,
        )

    def get_ticket_info(self, ticket_id):
        ticket_permalink = settings.POWERDISPATCHER_TICKET_URL.format(
            ticket_id=ticket_id
        )
        self.navigate_to(ticket_permalink)

        self.sleep(1)

        created_datetime_str = (
            WebDriverWait(self.driver, timeout=20)
            .until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//span[contains(@class, 'datetime-month')]/parent::td")
                )
            )
            .text
        )

        # Expected format Oct 03 2022 09:38 AM EDT
        created_datetime_obj = get_datetime_obj_from_str(
            created_datetime_str, "%b %d %Y %I:%M %p"
        )

        job_description_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "job_desc"))
        )
        job_description_selector = Select(job_description_element)
        job_description_str = job_description_selector.first_selected_option.text

        customer_phone = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "phone1"))
        )
        customer_phone_str = customer_phone.get_attribute("value")

        technician = self.get_ticket_technician()

        company = (
            WebDriverWait(self.driver, timeout=20)
            .until(
                EC.presence_of_element_located(
                    (By.ID, "select2-ddJobCompany-container")
                )
            )
            .text
        )

        zip_code = (
            WebDriverWait(self.driver, timeout=20)
            .until(EC.presence_of_element_located((By.ID, "zip")))
            .get_attribute("value")
        )

        alternative_source = (
            WebDriverWait(self.driver, timeout=20)
            .until(EC.presence_of_element_located((By.XPATH, "//input[@name='item']")))
            .get_attribute("value")
        )

        address = (
            WebDriverWait(self.driver, timeout=20)
            .until(EC.presence_of_element_located((By.ID, "address")))
            .get_attribute("value")
        )

        job_date_element = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "job_date"))
        )

        # Expected format 2022-10-20
        job_date_str = job_date_element.get_attribute("value")
        job_date_obj = datetime.datetime.strptime(job_date_str, "%Y-%m-%d")

        status, who_canceled_str, why_canceled_str = self.get_ticket_status()

        technician_parts = self.driver.find_element(By.NAME, "txtParts").get_attribute(
            "value"
        )
        if technician_parts:
            technician_parts = Decimal(technician_parts)
        else:
            technician_parts = 0

        company_parts = 0
        try:
            company_parts_elements = WebDriverWait(self.driver, timeout=2).until(
                EC.presence_of_all_elements_located((By.ID, "compparts"))
            )
            for part in company_parts_elements:
                value = part.get_attribute("value")
                company_parts += Decimal(value)
        except Exception:
            pass

        cash_payment = 0
        try:
            cash_payments = WebDriverWait(self.driver, timeout=2).until(
                EC.presence_of_all_elements_located((By.ID, "cashamount"))
            )
            for payment in cash_payments:
                value = payment.get_attribute("value")
                cash_payment += Decimal(value)
        except Exception:
            pass

        credit_payment = 0
        try:
            credit_payments = WebDriverWait(self.driver, timeout=2).until(
                EC.presence_of_all_elements_located((By.ID, "amount"))
            )
            for payment in credit_payments:
                value = payment.get_attribute("value")
                credit_payment += Decimal(value)
        except Exception:
            pass

        # LOG PAGE
        logs_btn = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located((By.ID, "addjob-menu-comments"))
        )
        logs_btn.click()
        comments_child_elements = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[@id='paneComments']/table[2]/tbody/tr/td[2]/*")
            )
        )
        date_label = ""

        created_by = None
        closed_by = None
        sent_time = None
        accepted_time = None
        first_call_time = None
        closed_time = None
        closed_by_titles = ["job canceled", "job closed", "job delayed"]
        for comment_child_element in comments_child_elements:
            element_class = comment_child_element.get_attribute("class")
            if element_class == "date-bar":
                date_label = comment_child_element.text
            elif element_class == "comment":
                comment_title = comment_child_element.find_element(
                    By.XPATH, "./tbody/tr/td[2]/div[2]/div/span"
                ).text.strip()
                lower_comment_title = comment_title.lower()
                if lower_comment_title == "job comment created":
                    comment_content = comment_child_element.find_element(
                        By.XPATH, "./tbody/tr/td[2]/div[2]/div/pre"
                    ).text
                    match_found = re.search(r"ACCEPTED job", comment_content)
                    if match_found and not accepted_time:
                        accepted_time = (
                            date_label
                            + " "
                            + comment_child_element.find_element(
                                By.XPATH, "./tbody/tr/td[2]/div[1]/span"
                            ).text
                        )
                    match_found = re.search(r"CLOSED job", comment_content)
                    if match_found and not closed_time:
                        closed_time = (
                            date_label
                            + " "
                            + comment_child_element.find_element(
                                By.XPATH, "./tbody/tr/td[2]/div[1]/span"
                            ).text
                        )
                    if technician:
                        match_found = re.search(r"To: ", comment_content)
                        if match_found and not sent_time:
                            sent_time = (
                                date_label
                                + " "
                                + comment_child_element.find_element(
                                    By.XPATH, "./tbody/tr/td[2]/div[1]/span"
                                ).text
                            )
                elif lower_comment_title == "job created":
                    created_by = comment_child_element.find_element(
                        By.XPATH, "./tbody/tr/td[2]/div[1]/span[2]"
                    ).text
                    comment_content = comment_child_element.find_element(
                        By.XPATH, "./tbody/tr/td[2]/div[2]/div/pre"
                    ).text
                    match_found = re.search(
                        r"Job sent to {techinian}".format(techinian=technician),
                        comment_content,
                    )
                    if match_found and not sent_time:
                        sent_time = (
                            date_label
                            + " "
                            + comment_child_element.find_element(
                                By.XPATH, "./tbody/tr/td[2]/div[1]/span"
                            ).text
                        )
                elif lower_comment_title == "conference created" and not sent_time:
                    first_call_time = (
                        date_label
                        + " "
                        + comment_child_element.find_element(
                            By.XPATH, "./tbody/tr/td[2]/div[1]/span"
                        ).text
                    )
                elif lower_comment_title in closed_by_titles and not closed_by:
                    closed_by = comment_child_element.find_element(
                        By.XPATH, "./tbody/tr/td[2]/div[1]/span[2]"
                    ).text

        sent_at = None
        accepted_at = None
        first_call_at = None
        closed_at = None
        # ipdb.set_trace()

        # Expected format: Monday, September 19 2022 03:30 PM EDT
        expected_pattern = "%A, %B %d %Y %I:%M %p"
        if sent_time:
            sent_at = get_datetime_obj_from_str(sent_time, expected_pattern)
        if accepted_time:
            accepted_at = get_datetime_obj_from_str(accepted_time, expected_pattern)
        if first_call_time:
            first_call_at = get_datetime_obj_from_str(first_call_time, expected_pattern)
        if closed_time:
            closed_at = get_datetime_obj_from_str(closed_time, expected_pattern)

        (
            alternative_technician,
            follow_up_given_by_alternative_technician,
            follow_up_strategy_successfull,
        ) = self.get_ticket_follow_up_info()

        ticket_data = {
            "powerdispatch_ticket_id": ticket_id,
            "customer_phone": customer_phone_str,
            "address": address,
            "zip_code": zip_code,
            "alternative_source": alternative_source,
            "technician": technician,
            "job_description": job_description_str,
            "company": company,
            "job_date": job_date_obj,
            "status": status,
            "created_by": created_by,
            "closed_by": closed_by,
            "credit_payment": credit_payment,
            "cash_payment": cash_payment,
            "technician_parts": technician_parts,
            "company_parts": company_parts,
            "created_at": created_datetime_obj,
            "sent_at": sent_at,
            "accepted_at": accepted_at,
            "first_call_at": first_call_at,
            "closed_at": closed_at,
            "who_canceled": who_canceled_str,
            "why_canceled": why_canceled_str,
            "alternative_technician": alternative_technician,
            "follow_up_given_by_alternative_technician": follow_up_given_by_alternative_technician,
            "follow_up_strategy_successfull": follow_up_strategy_successfull,
        }

        return ticket_data

    def get_job_descriptions(self):
        all_job_descriptions_permalink = (
            "https://lite.serviceslogin.com/settings_jobdesc.php?enabled=2"
        )
        self.navigate_to(all_job_descriptions_permalink)
        job_description_rows = WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//table[@id='settings-item-table']/descendant::tr")
            )
        )
        job_description_rows = job_description_rows[1:]

        job_descriptions = []
        for job_description_row in job_description_rows:
            data = job_description_row.find_elements(By.XPATH, "./descendant::td")
            description = data[0].text
            category = data[2].text
            enabled = data[3].find_element(By.XPATH, "./descendant::span").text
            job_description_dict = {
                "description": description,
                "category": category,
                "enabled": enabled,
            }
            job_descriptions.append(job_description_dict)
        return job_descriptions

    def close_driver(self):
        self.log("Closing driver")

        try:
            self.driver.quit()
            self.driver = None
        except Exception:
            pass
