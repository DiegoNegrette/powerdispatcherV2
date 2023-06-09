import datetime

from dateutil import relativedelta


def get_datetime_obj_from_str(datetime_str, pattern):
    cleaned_str = datetime_str.strip().rsplit(' ', 1)[0]
    datetime_obj = datetime.datetime.strptime(cleaned_str, pattern)
    return datetime_obj


def months_difference_between_dates(end_date, start_date):
    # Get the relativedelta between two dates
    delta = relativedelta.relativedelta(end_date, start_date)

    # get months difference
    res_months = delta.months + (delta.years * 12)

    return res_months


def trunc_date(someDate):
    return someDate.replace(day=1)
