__author__ = 'nmew'
import jinja2
from datetime import datetime
import time
import pytz


def timestampformat(timestampin, formatin, formatout, tzin='America/New_York', tzout='America/Los_Angeles'):
    full_timestamp = time.mktime(time.strptime(timestampin, formatin))
    datet = pytz.timezone(tzin).localize(datetime.fromtimestamp(full_timestamp))
    if datet.hour > 0:
        datet = datet.astimezone(pytz.timezone(tzout))
    return datet.strftime(formatout)


jinja2.filters.FILTERS['timestampformat'] = timestampformat