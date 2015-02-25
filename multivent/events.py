__author__ = 'yeti'
import datetime


class Event(object):
    def __init__(self, dates, name, **kwargs):
        if type(dates) == tuple:
            self.start_date = dates[0]
            self.end_date = dates[1]
        elif type(dates) == datetime.date:
            self.start_date = dates
            self.end_date = dates

        self.dates = (self.start_date, self.end_date)
        self.name = name
        self.description = kwargs.get("description", None)
