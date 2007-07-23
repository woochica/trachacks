# -*-coding:utf-8-*-

# Module caltools: domain logic for handling days & times.

import calendar
import time

def next_day (struct_time):
    tm_year, tm_mon, tm_day = struct_time[:3]
    days_in_month = calendar.monthrange(tm_year, tm_mon)[1]

    tm_day += 1
    if tm_day > days_in_month:
        tm_day = 1
        tm_mon += 1
        if tm_mon > 12:
            tm_mon = 1
            tm_year += 1

    return (tm_year, tm_mon, tm_day) + struct_time[3:]

def relative_day(week_start, which_day):
    d_year, d_doy = week_start[0], week_start[-2]
    doy = d_doy + which_day
    if doy < 1:
        d_year -= 1
        doy += 365 + int (calendar.isleap (d_year))
    elif doy > 365 + int (calendar.isleap (d_year)):
        doy -= 365 + int (calendar.isleap (d_year))
        d_year += 1
    day = time.strptime (str(d_year) + str(doy), "%Y%j")
    return day


def strptimeopt (string, *formats):
    """
    Each format may be either a string, or a tuple (string, callback).
    strptime result of the first matching format is returned.  If the
    format has assigned a callback, it is first called with the result
    of strptime, and result of the callback is then returned.
    """

    import types
    assert formats, "Non-empty list of formats required."
    err = None

    for format in formats:
        if type(format) == types.TupleType:
            format, callback = format
        else:
            callback = lambda x:x

        try:
            return callback(time.strptime(string, format))
        except ValueError, e:
            err = e

    raise err


def parse_time_begin_end (begin_string, end_string):
    begin_time = strptimeopt(begin_string,
                             "%Y/%m/%d %H:%M",
                             "%Y/%m/%d")

    # If end time is defined by Y/m/d, it defaults to the
    # /end/ of this day, which we conveniently translate
    # as the beginning of the next day.
    end_time = strptimeopt(end_string,
                           "%Y/%m/%d %H:%M",
                           ("%Y/%m/%d", next_day))

    begin_stamp = int(time.mktime(begin_time))
    end_stamp = int(time.mktime(end_time))

    return begin_time, end_time, begin_stamp, end_stamp

def get_week_range(date):
    """
    Answer the tuple (start, end) with timestamps of start and end of
    the week that contains given date.
    """

    # If there is a simpler way to do this, let me know.  For now...
    d_year, d_doy, d_dow = date[0], date[-2], date[-3]

    doy_start = d_doy - d_dow
    y_start = d_year
    if doy_start < 1:
        y_start -= 1
        doy_start += 365 + int (calendar.isleap (y_start))

    doy_end = d_doy - d_dow + 7
    y_end = d_year
    if doy_end > 365 + int (calendar.isleap (y_end)):
        doy_end -= 365 + int (calendar.isleap (y_end))
        y_end += 1

    week_start = time.strptime (str(y_start) + str(doy_start), "%Y%j")
    week_end = time.strptime (str(y_end) + str(doy_end), "%Y%j")
    return week_start, week_end

def get_month_range(date):
    """
    Answer the tuple (start, end) with timestamps of start and end of
    the month that contains given date.
    """

    d_year, d_month = date[0], date[1]
    month_start = tuple([d_year, d_month, 1] + [0 for _ in date[3:]])
    d_month = d_month + 1
    if d_month > 12:
        d_year += 1
        d_month = 1
    month_end = tuple([d_year, d_month, 1] + [0 for _ in date[3:]])
    return month_start, month_end
