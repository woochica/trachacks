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

# Each format may be either a string, or a tuple (string, callback).
# strptime result of the first matching format is returned.  If the
# format has assigned a callback, it is first called with the result
# of strptime, and result of the callback is then returned.
def strptimeopt (string, *formats):
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
