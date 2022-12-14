import datetime
from decimal import Decimal
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from powerdispatcher.conf import settings

from powerdispatcher.models import ProjectConfiguration
from powerdispatcher.scraper.base_mixing import ScraperBaseMixin
from powerdispatcher.utils import get_datetime_obj_from_str, trunc_date


class PowerdispatchSiteScraper(ScraperBaseMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        project_configuration = ProjectConfiguration.objects.get()
        self.current_account = {
            'account': project_configuration.powerdispatch_account,
            'username': project_configuration.powerdispatch_username,
            'password': project_configuration.powerdispatch_password,
        }
        self.account_identifier = "powerdispatch"
        self.webdriver_container_host = 'docker-host'
        self.webdriver_container_port = None
        self.blocked_domains = []

    def get_default_options(self):
        options_headers = ['--disable-notifications']
        initialize_options = {
            'chrome': webdriver.ChromeOptions,
            'firefox': webdriver.FirefoxOptions,
        }
        options_headers += ['--headless', '--no-sandbox'] if settings.HEADLESS else []  # noqa
        OptionClass = initialize_options.get(self.browser_type)
        options = OptionClass()

        options.add_argument('--start-maximized')

        for options_header in options_headers:
            options.add_argument(options_header)

        return options

    def get_chrome_options(self, options):

        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option(
            'excludeSwitches', ['enable-automation']
        )
        options.add_argument('--disable-geolocation')

        # options.add_argument(f'--user-data-dir=/home/seluser/.config/google-chrome/{user_data_dir_name}')

        prefs = dict()

        # disable geolocation
        prefs['profile.default_content_setting_values.geolocation'] = 2

        # disable "save password?" prompt
        prefs['credentials_enable_service'] = False
        prefs['profile.password_manager_enabled'] = False

        # disable webRTC to avoid real-IP leak
        prefs['webrtc.ip_handling_policy'] = 'disable_non_proxied_udp'
        prefs['webrtc.multiple_routes_enabled'] = False
        prefs['webrtc.nonproxied_udp_enabled'] = False

        # Change Language to English (Does not work for XPATH)
        # prefs['translate_whitelists'] = {'uk': 'en'}
        # prefs['translate'] = {'enabled': 'true'}

        options.add_experimental_option('prefs', prefs)

        # some assets are not worth loading and/or take too much time to load
        if len(self.blocked_domains) > 0:
            host_resolver_rules = ', '.join([
                f'MAP {d} 127.0.0.1' for d in self.blocked_domains
            ])
            options.add_argument(f'--host-resolver-rules={host_resolver_rules}')  # noqa

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
            raise Exception(f'Browser not supported: {self.browser_type}')

        return options

    def get_driver(self, options):
        initialize_driver = {
            'remote+firefox': webdriver.Remote,
            'remote+chrome': webdriver.Remote,
            'local+chrome': webdriver.Chrome,
        }
        eligible_capabilities = {
            'chrome': DesiredCapabilities.CHROME,
            'firefox': DesiredCapabilities.FIREFOX,
        }
        connection_options = {
            'local': settings.WEB_DRIVER_PATH,
            'remote': self.webdriver_url,
        }

        primary_identifier = f'{settings.CONNECTION_TYPE}+{self.browser_type}'

        DriverClass = initialize_driver[primary_identifier]

        desired_capabilities = eligible_capabilities[self.browser_type]

        return DriverClass(
            connection_options[settings.CONNECTION_TYPE],
            desired_capabilities=desired_capabilities,
            options=options
        )

    def init_driver(self):
        self.options = self.get_options()
        self.log(f"init_driver on {self.webdriver_url}")
        self.driver = self.get_driver(options=self.options)

    def login(self):
        self.navigate_to(settings.POWERDISPATCHER_POWER_DISPATCH_BASE_URL)

        WebDriverWait(self.driver, timeout=20).until(
            EC.presence_of_element_located(
                (By.NAME, "_submit")
            )
        )

        account = self.driver.find_element(By.NAME, '_account')
        account.send_keys(self.current_account["account"])
        username = self.driver.find_element(By.NAME, '_username')
        username.send_keys(self.current_account["username"])
        password = self.driver.find_element(By.NAME, '_password')
        password.send_keys(self.current_account["password"])
        submit = self.driver.find_element(By.NAME, '_submit')
        submit.click()
        self.sleep(2)

    def goto_search_menu(self):
        search_menu_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(text(), 'Search')]"
                )
            ),
            message="Search menu btn not found!"
        )
        search_menu_btn.click()
        self.sleep(2)

    def _filter_search(self, input_date, table_identifier):
        input_date_btn = self.driver.find_element(By.ID, f"{table_identifier}")
        input_date_btn.click()

        table_root = self.driver. \
            find_element(By.ID, f"{table_identifier}_root")

        MAX_CLICKS = 5 * 12  # 5 years
        clicks_performed = 0
        while clicks_performed <= MAX_CLICKS:

            table_header = table_root.find_element(
                By.XPATH, "./descendant::div[@class='picker__header']"
            )

            table_month = table_header. \
                find_element(By.XPATH, "./div[@class='picker__month']")
            table_year = table_header.  \
                find_element(By.XPATH, "./div[@class='picker__year']")
            prev_month_btn = table_header. \
                find_element(By.XPATH, "./div[@class='picker__nav--prev']")
            next_month_btn = table_header. \
                find_element(By.XPATH, "./div[@class='picker__nav--next']")

            DUMMY_DAY = 1

            currently_selected_date_str = (
                f"{DUMMY_DAY} {table_month.text} {table_year.text}"
            )
            currently_selected_date_obj = datetime.datetime.strptime(
                currently_selected_date_str, "%d %B %Y"
            ).date()

            first_day_of_currently_selected \
                = trunc_date(currently_selected_date_obj)
            first_day_of_input_date = trunc_date(input_date)

            if first_day_of_currently_selected > first_day_of_input_date:
                prev_month_btn.click()
            elif first_day_of_currently_selected < first_day_of_input_date:
                next_month_btn.click()
            else:
                break
            clicks_performed += 1

        table_body = self.driver. \
            find_element(By.ID, f"{table_identifier}_table")

        input_date_str = input_date.strftime("%Y-%m-%d")

        target_day = table_body.find_element(
            By.XPATH,
            f"./tbody/descendant::div[@aria-label='{input_date_str}']"
        )

        target_day.click()

    def filter_search(self, start_date, end_date):
        self._filter_search(start_date, "txtDate1")
        self._filter_search(end_date, "txtDate2")
        submit_btn = self.driver.find_element(By.ID, "btnSubmit")
        submit_btn.click()

    def get_ticket_ids_from_search_result(self):
        MAX_PAGES = 1000  # TODO THIS SHOULD BE ADDED AS A CONFIG PARAMETER
        current_page = 1
        all_ticket_ids = []
        while current_page <= MAX_PAGES:
            try:
                search_result_table = self.driver. \
                    find_element(By.ID, "search-result-table")
            except NoSuchElementException:
                return all_ticket_ids
            current_page_jobs = search_result_table. \
                find_elements(By.XPATH, "./tbody[2]/tr")

            for job in current_page_jobs:
                ticket_id_element = job.find_element(By.XPATH, "./td[5]")
                ticket_id = ticket_id_element.text
                all_ticket_ids.append(ticket_id)

            try:
                next_page_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//button[contains(text(), 'Next')]"
                        )
                    ),
                    message="Next page btn not found!"
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

    def get_ticket_info(self, ticket_id):
        ticket_permalink = settings.POWERDISPATCHER_TICKET_URL. \
            format(ticket_id=ticket_id)
        self.navigate_to(ticket_permalink)

        created_datetime_str = self.driver.find_element(
            By.XPATH,
            "//span[contains(@class, 'datetime-month')]/parent::td"
        ).text

        # Expected format Oct 03 2022 09:38 AM EDT
        created_datetime_obj = get_datetime_obj_from_str(created_datetime_str, "%b %d %Y %I:%M %p")  # noqa

        job_description_element = self.driver.find_element(By.ID, "job_desc")
        job_description_selector = Select(job_description_element)
        job_description_str = job_description_selector.first_selected_option.text  # noqa

        customer_phone = self.driver.find_element(By.ID, "phone1")
        customer_phone_str = customer_phone.get_attribute("value")

        technician = self.driver.find_element(By.ID, "select2-ddTech-container").text  # noqa

        if 'select a technician' in technician.lower():
            technician = None

        company = self.driver.find_element(By.ID, "select2-ddJobCompany-container").text  # noqa

        zip_code = self.driver. \
            find_element(By.ID, "zip").get_attribute("value")
        address = self.driver. \
            find_element(By.ID, "address").get_attribute("value")

        job_date_element = self.driver.find_element(By.ID, "job_date")
        # Expected format 2022-10-20
        job_date_str = job_date_element.get_attribute("value")
        job_date_obj = datetime.datetime.strptime(job_date_str, "%Y-%m-%d")

        status_element = self.driver.find_element(By.ID, "ddStatus")
        status_selector = Select(status_element)
        status = status_selector.first_selected_option.text

        technician_parts = self.driver. \
            find_element(By.NAME, "txtParts").get_attribute("value")
        if technician_parts:
            technician_parts = Decimal(technician_parts)
        else:
            technician_parts = 0

        company_parts = 0
        try:
            company_parts_elements = self.driver.find_elements(By.ID, "compparts")  # noqa
            for part in company_parts_elements:
                value = part.get_attribute("value")
                company_parts += Decimal(value)
        except NoSuchElementException:
            pass

        cash_payment = 0
        try:
            cash_payments = self.driver.find_elements(By.ID, "cashamount")
            for payment in cash_payments:
                value = payment.get_attribute("value")
                cash_payment += Decimal(value)
        except NoSuchElementException:
            pass

        credit_payment = 0
        try:
            credit_payments = self.driver.find_elements(By.ID, "amount")
            for payment in credit_payments:
                value = payment.get_attribute("value")
                credit_payment += Decimal(value)
        except NoSuchElementException:
            pass

        if status == 'Canceled':
            who_canceled_element = self.driver.find_element(
                By.XPATH, "//*[@id='cancel_slide']/fieldset/select"
            )
            who_canceled_element_selector = Select(who_canceled_element)

            try:
                selected_option = \
                    who_canceled_element_selector.first_selected_option.text
                who_canceled_str = selected_option if selected_option else None  # noqa
            except NoSuchElementException:
                who_canceled_str = None

            why_canceled_element = self.driver.find_element(
                By.XPATH, "//*[@id='cancel_slide']/fieldset/input"
            )
            why_canceled_str = why_canceled_element.get_attribute("value")
            why_canceled_str = why_canceled_str if why_canceled_str else None
        else:
            who_canceled_str = None
            why_canceled_str = None

        # LOG PAGE
        logs_btn = self.driver.find_element(By.ID, "addjob-menu-comments")
        logs_btn.click()
        comments_child_elements = self.driver.find_elements(
            By.XPATH, "//*[@id='paneComments']/table[2]/tbody/tr/td[2]/*"
        )
        date_label = ""

        created_by = None
        closed_by = None
        sent_time = None
        accepted_time = None
        first_call_time = None
        closed_time = None
        closed_by_titles = ['job canceled', 'job closed', 'job delayed']
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
                        By.XPATH,
                        "./tbody/tr/td[2]/div[2]/div/pre"
                    ).text
                    match_found = re.search(r'ACCEPTED job', comment_content)
                    if match_found and not accepted_time:
                        accepted_time = date_label + " " + comment_child_element. \
                            find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span").text  # noqa;
                    match_found = re.search(r'CLOSED job', comment_content)
                    if match_found and not closed_time:
                        closed_time = date_label + " " + comment_child_element. \
                            find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span").text  # noqa;
                    if technician:
                        match_found = re.search(
                            r'To: ',  # noqa
                            comment_content
                        )
                        if match_found and not sent_time:
                            sent_time = date_label + " " + comment_child_element. \
                                find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span").text  # noqa;
                elif lower_comment_title == "job created":
                    created_by = comment_child_element. \
                        find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span[2]").text  # noqa
                    comment_content = comment_child_element.find_element(
                        By.XPATH,
                        "./tbody/tr/td[2]/div[2]/div/pre"
                    ).text
                    match_found = re.search(
                        r'Job sent to {techinian}'.format(techinian=technician),  # noqa
                        comment_content
                    )
                    if match_found and not sent_time:
                        sent_time = date_label + " " + comment_child_element. \
                            find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span").text  # noqa;
                elif lower_comment_title == "conference created" \
                        and not sent_time:
                    first_call_time = date_label + " " + comment_child_element. \
                        find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span").text  # noqa
                elif lower_comment_title in closed_by_titles \
                        and not closed_by:
                        closed_by = comment_child_element. \
                            find_element(By.XPATH, "./tbody/tr/td[2]/div[1]/span[2]").text  # noqa

        sent_at = None
        accepted_at = None
        first_call_at = None
        closed_at = None
        # ipdb.set_trace()

        # Expected format: Monday, September 19 2022 03:30 PM EDT
        expected_pattern = "%A, %B %d %Y %I:%M %p"
        if sent_time:
            sent_at = get_datetime_obj_from_str(
                sent_time, expected_pattern
            )
        if accepted_time:
            accepted_at = get_datetime_obj_from_str(
                accepted_time, expected_pattern
            )
        if first_call_time:
            first_call_at = get_datetime_obj_from_str(
                first_call_time, expected_pattern
            )
        if closed_time:
            closed_at = get_datetime_obj_from_str(
                closed_time, expected_pattern
            )

        ticket_data = {
            "powerdispatch_ticket_id": ticket_id,
            "customer_phone": customer_phone_str,
            "address": address,
            "zip_code": zip_code,
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
        }

        return ticket_data

    def get_job_descriptions(self):
        all_job_descriptions_permalink \
            = "https://lite.serviceslogin.com/settings_jobdesc.php?enabled=2"
        self.navigate_to(all_job_descriptions_permalink)
        job_description_rows = self.driver.find_elements(
            By.XPATH, "//table[@id='settings-item-table']/descendant::tr"
        )
        job_description_rows = job_description_rows[1:]

        job_descriptions = []
        for job_description_row in job_description_rows:
            data = job_description_row.find_elements(
                By.XPATH, "./descendant::td"
            )
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
        self.log('Closing driver')

        try:
            self.driver.quit()
            self.driver = None
        except Exception:
            pass
