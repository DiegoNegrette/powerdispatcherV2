import re

from powerdispatcher.models import (
    Branch,
    Customer,
    Date,
    Dispatcher,
    JobDescription,
    Location,
    Status,
    Technician,
    Ticket,
)


class PowerdispatchManager:

    def clean_phone(self, input_phone_str):
        new_phone_str = re.sub(r"\D", "", input_phone_str)
        phone_str = new_phone_str.strip()
        PHONE_MAX_LENGTH = 10
        phone_str = phone_str[-PHONE_MAX_LENGTH:]
        return phone_str

    def clean_zip_code(self, input_zip_code):
        new_zip_code = re.sub(r"\D", "", input_zip_code)
        zip_code = new_zip_code.strip()
        return zip_code

    def get_zip_code(self, zip_code):
        zip_code = self.clean_zip_code(zip_code)
        ZIP_CODE_LENGTH = 5
        if len(zip_code) != ZIP_CODE_LENGTH:
            zip_code = None
        else:
            zip_code = Location.objects.get(zip_code=zip_code)
        return zip_code

    def get_status(self, status_str, who_canceled, why_canceled):
        status_obj, _ = Status.objects.get_or_create(
            name=status_str,
            who_canceled=who_canceled,
            why_canceled=why_canceled,
        )
        return status_obj

    def upsert_customer(self, phone_str):
        phone = self.clean_phone(input_phone_str=phone_str)
        customer, _ = Customer.objects.get_or_create(phone=phone)
        return customer

    def upsert_job_description(self, job_description_str):
        description = self.clean_description(input_description=job_description_str)
        job_description_obj, _ = JobDescription.objects.get_or_create(
            description=description
        )
        return job_description_obj

    def upsert_dispatcher(self, dispatcher_str):
        dispatcher_obj, _ = Dispatcher.objects.get_or_create(name=dispatcher_str)
        return dispatcher_obj

    def upsert_technician(self, technician_str):
        technician_obj, _ = Technician.objects.get_or_create(
            name=technician_str,
        )
        return technician_obj

    def upsert_branch(self, company_str):
        company_obj, _ = Branch.objects.get_or_create(name=company_str)
        return company_obj

    def get_calendar_date(self, job_date):
        date = Date.objects.get(
            year=job_date.year,
            month_number=job_date.month,
            day=job_date.day,
        )
        return date

    def get_obj_dict_from_ticket_info(self, ticket_info):
        powerdispatch_ticket_id = ticket_info["powerdispatch_ticket_id"]
        customer = self.upsert_customer(ticket_info["customer_phone"])
        status = self.get_status(
            status_str=ticket_info["status"],
            who_canceled=ticket_info["who_canceled"],
            why_canceled=ticket_info["why_canceled"],
        )
        technician = self.upsert_technician(ticket_info["technician"])
        job_description = self.upsert_job_description(ticket_info["job_description"])
        created_by = self.upsert_dispatcher(ticket_info["created_by"])
        closed_by = None
        if ticket_info["closed_by"]:
            closed_by = self.upsert_dispatcher(ticket_info["closed_by"])
        job_date = self.get_calendar_date(ticket_info["job_date"])
        zip_code = self.get_zip_code(ticket_info["zip_code"])
        address = None
        if ticket_info["address"] and len(ticket_info["address"]) > 3:
            address = ticket_info["address"]
        branch = self.upsert_branch(ticket_info["company"])
        alternative_technician = (
            self.upsert_technician(ticket_info["alternative_technician"])
            if ticket_info["alternative_technician"]
            else None
        )
        ticket_obj_dict = {
            "powerdispatch_ticket_id": powerdispatch_ticket_id,
            "customer": customer,
            "status": status,
            "technician": technician,
            "job_description": job_description,
            "created_by": created_by,
            "closed_by": closed_by,
            "branch": branch,
            "zip_code": zip_code,
            "alternative_source": ticket_info["alternative_source"],
            "address": address,
            "credit_payment": ticket_info["credit_payment"],
            "cash_payment": ticket_info["cash_payment"],
            "technician_parts": ticket_info["technician_parts"],
            "company_parts": ticket_info["company_parts"],
            "job_date": job_date,
            "created_at": ticket_info["created_at"],
            "sent_at": ticket_info["sent_at"],
            "accepted_at": ticket_info["accepted_at"],
            "first_call_at": ticket_info["first_call_at"],
            "closed_at": ticket_info["closed_at"],
            "alternative_technician": alternative_technician,
            "follow_up_given_by_alternative_technician": ticket_info[
                "follow_up_given_by_alternative_technician"
            ],
            "follow_up_strategy_successfull": ticket_info[
                "follow_up_strategy_successfull"
            ],
        }
        return ticket_obj_dict

    def upsert_ticket(self, ticket_info):
        ticket_obj_dict = self.get_obj_dict_from_ticket_info(ticket_info)
        powerdispatch_ticket_id = ticket_obj_dict.pop("powerdispatch_ticket_id")
        ticket, created = Ticket.objects.get_or_create(
            powerdispatch_ticket_id=powerdispatch_ticket_id,
            defaults=ticket_obj_dict,
        )
        return ticket, created

    def clean_description(self, input_description):
        new_description = re.sub(r"\[.+\]", "", input_description)
        description = new_description.strip()
        return description

    def get_obj_dict_from_job_description_info(self, job_description_info):
        description = self.clean_description(
            input_description=job_description_info["description"]
        )
        enabled = False
        if job_description_info["enabled"] == "Enabled":
            enabled = True
        job_description_obj_dict = {
            "description": description,
            "category": job_description_info["category"],
            "enabled": enabled,
        }
        return job_description_obj_dict

    def upsert_job_descriptions(self, job_description_info):
        job_description_obj_dict = self.get_obj_dict_from_job_description_info(
            job_description_info
        )
        description = job_description_obj_dict.pop("description")
        job_description, created = JobDescription.objects.get_or_create(
            description=description,
            defaults=job_description_obj_dict,
        )

        if not created:
            job_description.category = job_description_obj_dict["category"]
            job_description.enabled = job_description_obj_dict["enabled"]
            job_description.save(update_fields=["category", "enabled"])

        return job_description, created
