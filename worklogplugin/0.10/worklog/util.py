from datetime import datetime

# Stolen from Trac trunk :)
def pretty_timedelta(time1, time2=None, full=False):
    """Calculate time delta (inaccurately, only for decorative purposes ;-) for
    prettyprinting. If time1 is None, the current time is used."""
    if not time1: time1 = datetime.now()
    if not time2: time2 = datetime.now()
    if time1 > time2:
        time2, time1 = time1, time2
    units = ((3600 * 24 * 365, 'year',   'years'),
             (3600 * 24 * 30,  'month',  'months'),
             (3600 * 24 * 7,   'week',   'weeks'),
             (3600 * 24,       'day',    'days'),
             (3600,            'hour',   'hours'),
             (60,              'minute', 'minutes'))
    diff = time2 - time1
    age_s = int(diff.days * 86400 + diff.seconds)
    if age_s < 60:
        return '%i second%s' % (age_s, age_s != 1 and 's' or '')
    rv = ''
    for u, unit, unit_plural in units:
        r = float(age_s) / float(u)
        if r >= 0.9:
            r = int(round(r))
            tmp_rv = '%d %s' % (r, r == 1 and unit or unit_plural)
            if not full:
                return tmp_rv
            if rv:
                rv += ', '
            rv += tmp_rv
            age_s = float(age_s) - (r * float(u)) 
    return rv

