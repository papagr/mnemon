import datetime


def now():
    return datetime.datetime.now()


def past_datetime_by(number_of_days):
    return now() - datetime.timedelta(days=number_of_days)
