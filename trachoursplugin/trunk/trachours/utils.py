# -*- coding: utf-8 -*-

import calendar
import datetime

def get_all_users(env):
    """return the names of all known users in the trac environment"""
    return [ i[0] for i in env.get_known_users() ]

def truncate_to_month(day, month, year):
    """
    return the day given if its valid for the month + year,
    or the end of the month if the day exceeds the month's number of days
    """
    # enable pasing of strings
    year = int(year)
    month = int(month)
    maxday = calendar.monthrange(year, month)[-1]
    if maxday < int(day):
        return maxday
    return day

def urljoin(*args):
    return '/'.join(arg.strip('/') for arg in args)

def get_date(year, month=1, day=1, end_of_day=False):
    if not month:
        month = 1
    if not day:
        day = 1

    # TODO: error handling for int conversion
    year = int(year)
    month = int(month)
    day = int(day)
    
    if end_of_day:
        return datetime.datetime(year, month, truncate_to_month(day, month, year), 23, 59, 59)
    else:
        return datetime.datetime(year, month, truncate_to_month(day, month, year))
    
