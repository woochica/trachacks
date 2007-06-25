from datetime import datetime

def get_latest_task(db, authname):
    if authname == 'anonymous':
        return None
    
    cursor = db.cursor()
    sql = "SELECT MAX(lastchange) FROM work_log WHERE user='%s'" % (authname)
    cursor.execute(sql)
    row = cursor.fetchone()
    if not row or not row[0]:
        return None
    
    lastchange = row[0]
    
    task = {}
    sql = "SELECT user,ticket,lastchange,starttime,endtime FROM work_log WHERE user='%s' AND lastchange=%s" % (authname, lastchange)
    cursor.execute(sql)
    for user,ticket,lastchange,starttime,endtime in cursor:
        task['user'] = user
        task['ticket'] = ticket
        task['lastchange'] = lastchange
        task['starttime'] = starttime
        task['endtime'] = endtime
    return task

# Stolen from Trac trunk :)
def pretty_timedelta(time1, time2=None, resolution=None):
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
    if resolution and age_s < resolution:
        return ''
    if age_s < 60:
        return '%i second%s' % (age_s, age_s != 1 and 's' or '')
    for u, unit, unit_plural in units:
        r = float(age_s) / float(u)
        if r >= 0.9:
            r = int(round(r))
            return '%d %s' % (r, r == 1 and unit or unit_plural)
    return ''

