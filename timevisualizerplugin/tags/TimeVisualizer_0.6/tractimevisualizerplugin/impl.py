"""This file provides actual Burndown renderer implementation

The actual implementation was moved to this implementation file - this way the
wrapper can use reload implementation on each request. This is needed when using
mod python - another option would be cgi but it is slow. With reloading & mod
python the development becomes extremely fast - modify source, save & reload web
page.
"""

# ==============================================================================
class NullOut:
    def write(self, data):
        pass

# ==============================================================================
import trac
from calendar import timegm
import time
import sys
import StringIO
import datetime

#http://en.wikipedia.org/wiki/ISO_8601
#http://wiki.python.org/moin/WorkingWithTime
#http://seehuhn.de/pages/pdate
#http://cheeseshop.python.org/pypi/iso8601/0.1.2
#http://www.w3.org/TR/NOTE-datetime
#http://hydracen.com/dx/iso8601.htm
#http://www.cl.cam.ac.uk/%7emgk25/iso-time.html
# 12:00Z = 13:00+01:00 = 0700-0500

# parse period, e.g. P18Y9M4DT11H9M8S
# return seconds.
# note: this gives very approximate result, e.g. 1 month is very obfuscating == 365/12 D
def parse_iso8601_period(text):
    result = 0
    text = text.replace('P','')
    text = text.replace('T','')
    text = text.upper()
    # => 18Y9M4D11H9M8S
    a = (
      'Y', 365 * 24 * 60 * 60,
      'M', 365 * 24 * 60 * 60 / 12,
      'W', 7 * 24 * 60 * 60,
      'D', 24 * 60 * 60,
      'H', 60 * 60,
      'M', 60,
      'S', 1 )
    for i in range(0,len(a),2):
        tmp = text.split(a[i])
        if len(tmp) > 1:
            text = tmp[1]
            result += int(tmp[0]) * a[i+1]
    return result

def parse_iso8601_datetime(text):
    # todo: expecting zero zone => let user pass in his/her zone?
    seconds = None
    text = text.strip()
    format = ''
    for append in ('%Y', '-%m', '-%d', ' %H', ':%M', ':%S'):
        format += append
        try:
            date = time.strptime(text, format)
            seconds = timegm(date)
            break
        except ValueError:
            continue
    if seconds == None:
        raise ValueError, "'%s' is not ISO 8601 date format (YYYY-MM-DD hh:mm:ss)." % text
    return seconds

def format_iso8601_datetime(secs):
    return time.strftime('%Y-%m-%d %H:%M:%SZ',time.gmtime(secs))

# this wrapper is needed for trac.util.parse_date, cos trac 0.10 does return seconds but 0.11 returns datetime object
def trac_parse_date(obj):
    result = trac.util.parse_date(obj)
    if isinstance(result,datetime.datetime):
        result = timegm(result.timetuple())
    return result

# ==============================================================================
def build_svg(db, options):
    """trac db instance (usually taken from environment) is mandatory."""
    def strtotype(val, type):
        if isinstance(val, str) or isinstance(val, unicode):
            return type(val)
        return val

    # todo: take filters as functions => let caller to build them
    targetmilestone=options.get('targetmilestone', None)
    targetticket=strtotype(options.get('targetticket', None), int)
    targetcomponent=options.get('targetcomponent', None)
    timestart=strtotype(options.get('timestart', 0), int)
    timeend=strtotype(options.get('timeend',0), int)
    datestart=options.get('datestart', None)
    dateend=options.get('dateend', None)
    hidedates=options.get('hidedates')
    hidehours=options.get('hidehours')
    calc_fields_str = options.get('calc_fields')
    calc_fields = calc_fields_str.split('-')

    print "********************** serving ***********************"
    format_datetime = trac.util.format_datetime
    parse_date = trac_parse_date
    parse_interval = int

    if options.get('time_format') == 'iso8601':
        format_datetime = format_iso8601_datetime
        parse_date = parse_iso8601_datetime
        parse_interval = parse_iso8601_period

    time_interval=strtotype(options.get('timeinterval', 86400), parse_interval)
    assert time_interval > 0, "'timeinterval' must be at least one second, now %d" % time_interval

    # override timestart if datestart given
    try:
        if datestart: timestart = parse_date(datestart)
    except Exception:
        raise Exception, "invalid startdate: " + str(sys.exc_info()[1])

    # override timeend if dateend given
    try:
        if dateend: timeend = parse_date(dateend)
    except Exception:
        raise Exception, "invalid dateend: " + str(sys.exc_info()[1])

    # this dict stores tickets. Tickets are updated on each 'revision' visited - so this contains snapshot of tickets at certain time
    tickets = {}

    def tofloat(obj):
        """Converts object to float. Accepts bot dot and comma as decimal separator. If object is None or empty string, 0.0 is returned."""
        if isinstance(obj,float):
            return obj
        if not obj: # None or empty string
            return 0.0
        if isinstance(obj,str) or isinstance(obj,unicode):
            return float(obj.replace(",","."))
        return float(obj) #fallback

    def calc_hours(tickets):
        """Calculates totalhours of tickets on current tickets state taking filters in the account."""
        result = 0.0
        for ticket in tickets.values():
            if targetmilestone and ticket['milestone'] != targetmilestone: continue
            if targetticket and ticket['id'] != targetticket: continue
            if targetcomponent and ticket['component'] != targetcomponent: continue
            if len(calc_fields) == 2:
                result += tofloat(ticket[calc_fields[0]]) - tofloat(ticket[calc_fields[1]])
            else:
                result += tofloat(ticket[calc_fields[0]])
        return result

    cursor = db.cursor()

    # ----------------------------------------------------
    # fetch the last known state (HEAD revision) of tickets and store to memory
    # ----------------------------------------------------

    ticket_fields = (
        'id',
#        'type',
#        'time',       # created
#        'changetime', # modified
        'component',
#        'severity',
#        'priority',
#        'owner',
#        'reporter',
#        'cc',
#        'version',
        'milestone',
#        'status',
#        'resolution',
#        'summary',
#        'description',
#        'keywords'
        )

    # todo: fetch from db/env
    custom_ticket_fields = calc_fields

    sql = StringIO.StringIO()
    sql.write('SELECT \n')
    for i in range(len(ticket_fields)):
        if i>0 : sql.write(',\n')
        sql.write('  t.%s AS %s' % (ticket_fields[i], ticket_fields[i]))

    for i in range(len(custom_ticket_fields)):
        sql.write(',\n')
        sql.write('  j%d.value AS %s' % (i, custom_ticket_fields[i]))

    sql.write('\nFROM ticket t\n')
    for i in range(len(custom_ticket_fields)):
        sql.write("  LEFT OUTER JOIN ticket_custom j%d ON(t.id=j%d.ticket AND j%d.name='%s')\n" % (i,i,i,custom_ticket_fields[i]))

    sql.write('ORDER BY t.id')
    #print sql.getvalue()

    cursor.execute(sql.getvalue())
    tickets = {}
    all_fields = []
    all_fields += ticket_fields
    all_fields += custom_ticket_fields
    it = cursor.fetchall()
    for row in it:
        ticket = {}
        tickets[row[0]] = ticket
        for i in range(len(all_fields)):
            ticket[all_fields[i]] = row[i]

    # ----------------------------------------------------
    # process timestamps from last ticket change/creation
    # to first ticket created and build x/y-pairs to result array
    # ----------------------------------------------------

    result = []
    def process_time(time):
        hours = calc_hours(tickets)
        if len(result) >= 2 and result[-1] == hours:
            # update timestamp
            result[-2] = time
        elif len(result) < 2 or result[-1] != hours:
            # data changed from previous item -> write row
            result.append(time)
            result.append(hours)

    def process_ticket_create(t, id):
        del tickets[id]

    process_ticket_change_sql = """
        SELECT field, oldvalue
        FROM ticket_change
        WHERE time=%d AND ticket=%d AND field IN (""" + "'" + "','".join(all_fields) + "'" + """)
        ORDER BY time desc"""

    def process_ticket_change(t, id):
        sql = process_ticket_change_sql % (t,id)

        cursor.execute(sql)
        data = cursor.fetchall()
        for (field,oldvalue) in data:
            # we iterate backwards, thus we save old values
            tickets[id][field] = oldvalue

    # -- find out timestamps (revisions) and bind processors for them

    timestamps = {}

    # creation times
    cursor.execute("SELECT DISTINCT time, id from ticket ORDER BY time")
    for line in cursor.fetchall():
        timestamps[int(line[0])] = [(process_ticket_create, int(line[1]))]

    # modified times
    cursor.execute("SELECT DISTINCT time, ticket from ticket_change ORDER BY time")
    for line in cursor.fetchall():
        item = timestamps.get(int(line[0]),[])
        item.insert(0, (process_ticket_change, int(line[1])))
        timestamps[int(line[0])] = item

    # -- process each timestamp from oldest to newest (direction is importat cos we know only the latest state)

    tmp = [] + timestamps.keys()
    tmp.sort()
    tmp.reverse() # from oldest to youngest
    for t in tmp:
        process_time(t)
        for processor in timestamps[t]:
            processor[0](t, processor[1])

    # ----------------------------------------------------
    # generate graph based on results
    # ----------------------------------------------------

    NO_DATA = \
"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">
    <text x="50%" y="50%" text-anchor="middle" style="font-family:verdana;">No data</text>
</svg>
"""
    if len(result) < 4:
        return NO_DATA

    # last item is zero and timestamp is updated to first ticket creation, so it needs to be 'scaled' to first item where hours change
    result[-2] = result[-4]

    #print, "result=",str(result)

    # if start or end times are defined, drop results outside of them
    if timestart:
        for i in range(0, len(result),2):
            if result[i] >= timestart: continue
            if i == 0:
                return NO_DATA
            result[i] = timestart
            result[i+1] = result[i-1]
            result = result[:i+2]
            break

    if timeend:
        starti = len(result)-2
        for i in range(starti, -2, -2):
            if result[i] <= timeend: continue
            if i == starti:
                return NO_DATA
            result[i] = timeend
            result[i+1] = result[i+3]
            result = result[i:]
            break

    # translate time from something big to origin (from timestart+n..timestart+n+x -> timestart .. timestart+x)
    # if timestart is zero (not give), the graph is translated using the smallest x-y pair in result
    smallesttime=timestart
    if smallesttime == 0:
        smallesttime = result[-2]
    for i in range(0, len(result),2):
        result[i] -= smallesttime

    largesttime = result[0] #largest time is result[0] because values were got from sorted sql resultset
    if timeend:
        largesttime = timeend - smallesttime

    maxhours = 0.1; # there was division by zero if all hours are zero (should not happen anymore though)
    for i in range(0, len(result),2):
        if result[i+1] > maxhours:
            maxhours = result[i+1]

    # todo: margin as percents
    #margin = 2

    fx = 100.0 / max(largesttime, 1)
    fy = 100.0 / max(maxhours, 1)

    svg =\
"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">

<svg width="100%" height="100%" version="1.1" xmlns="http://www.w3.org/2000/svg">
"""
    # draw time interval
    for i in range(largesttime, 0, -time_interval):
        svg += """<line x1="%f%%" y1="0%%" x2="%f%%" y2="100%%" style="stroke:rgb(150,255,255);stroke-width:3"/>\n""" % \
            (i * fx, i*fx)

    if not hidehours:
        hourlines=5
        step = float(maxhours) / hourlines
        if(step > 1): step = int(step)
        i=0.0
        while(i < maxhours):
            y = 100 - i * fy
            svg += '<line x1="0" y1="%f%%" x2="100%%" y2="%f%%" style="stroke:rgb(150,255,255);stroke-width:3"/>\n' % (y,y)
            if i > 0:
                svg += '<text x="0" y="%f%%" text-anchor="start" style="font-family:verdana;">%s</text>\n' %  (y, str(i))
            i += step

    #result= [1581,5,     0,2,     0,0]
    #result= [1581,5,     700,2,     300,4,  0,0]
    for i in range(0, len(result)-2, 2):
        svg += """<line x1="%f%%" y1="%f%%" x2="%f%%" y2="%f%%" style="stroke:rgb(0,200,0);stroke-width:3"/>\n""" % \
            (result[i] * fx, 100 - result[i+1] * fy, result[i] * fx, 100 - result[i+3] * fy)

        svg += """<line x1="%f%%" y1="%f%%" x2="%f%%" y2="%f%%" style="stroke:rgb(0,200,0);stroke-width:3"/>\n""" % \
            (result[i] * fx, 100 - result[i+3] * fy, result[i+2] * fx, 100 - result[i+3] * fy)

    if not hidedates:
        # draw graph start & end dates
        # http://www.w3.org/TR/SVG11/text.html#AlignmentProperties
        svg += '<text x="0" y="99%%" text-anchor="start" style="font-family:verdana;">%s</text>' % (format_datetime(smallesttime))
        svg += '<text x="100%%" y="99%%" text-anchor="end" style="font-family:verdana;">%s</text>' % (format_datetime(smallesttime+largesttime))

    svg += "</svg>\n"
    return svg

if __name__ == "__main__":
    "This is just for testing the stuff from command line"

    def build_svg_paramlist(db, **args):
        return build_svg(db, args)

    env = trac.env.open_environment("/var/scm/trac/tvdemo1")
    db = env.get_db_cnx()
    svg = build_svg_paramlist(db, milestone='milestone1', time_interval=3600*24, datestart="8/1/07", dateend="10/1/07")

    FILE = open("test.svg", "w")
    FILE.write(svg)
    FILE.close()

def process_request(plugin, req):
    """Renders a svg graph based on request attributes and returns a http response (or traceback in case of error)"""

    old_sys_stdout = sys.stdout

    import tractimevisualizerplugin
    if tractimevisualizerplugin.DEVELOPER_MODE:
        sys.stdout = StringIO.StringIO()
    else:
        sys.stdout = NullOut()
    try:
        req.send_response(200)
        req.send_header('Content-Type', "image/svg+xml")
        req.send_header('Last-Modified', trac.util.datefmt.http_date(time.time()))
        req.end_headers()

        if req.method != 'HEAD':
            db = plugin.env.get_db_cnx()
            args = req.args.copy()
            if not args.get('calc_fields'):
                args['calc_fields'] = plugin.env.config.get('timevisualizer','calc_fields','estimatedhours-totalhours')
            if not args.get('time_format'):
                args['time_format'] = plugin.env.config.get('timevisualizer','time_format', None)
            req.write(build_svg(db, args))
        raise trac.web.RequestDone
    finally:
        log = sys.stdout
        sys.stdout = old_sys_stdout
        if isinstance(log, StringIO.StringIO):
            plugin.log.debug(log.getvalue())
