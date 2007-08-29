"""This is the actual implementation of SVGRenderer component

The actual implementation was moved to this implementation file - this way the wrapper can use reload implementation on each request. This is needed when using mod python - another option would be cgi but it is slow. With reloading & mod python the development becomes extremely fast - modify source, save & reload web page.
"""

class NullOut:
    def write(self, data):
        pass

def build_svg(db, options, debug=None):
    """= Function build_svg =

This function does all the work. Options for method are:

 * db::trac database instance, usually taken from environment
 * targetmilestone - only tickets data bount to given milestone name is included
 * targetcomponent - only ticket data bound to given component name is included
 * targetticket - only data in given ticket # is included
 * timeinterval - time interval lines as seconds in graph, 3600 = 1h, 86400 = 1d
 * timestart - filters out ticket data before this timestamp
 * timeend - filters out ticket data after this timestamp
 * datestart - overrides timestart if passed, e.g. '8/14/07'
 * dateend - overrides timeend when passed - e.g. '8/20/07'
 * hidedates - any non empty string causes start and end times not to be rendered to the graph
 * hidehours - any non empty string causes hours not to be rendered to the graph
 
Note that filtering tickets that are not belonging to any milestone or component is not currently possible, because there is no way to indicate 'NULL' milestone or component!
"""

    if not debug:
        debug = NullOut()

    def strtotype(val, type):
        if isinstance(val, str) or isinstance(val, unicode):
            return type(val)
        return val

    targetmilestone=options.get('targetmilestone', None)
    targetticket=strtotype(options.get('targetticket', None), int)
    targetcomponent=options.get('targetcomponent', None)
    time_interval=strtotype(options.get('timeinterval', 3600*24), int)
    timestart=strtotype(options.get('timestart', 0), int)
    timeend=strtotype(options.get('timeend',0), int)
    datestart=options.get('datestart', None)
    dateend=options.get('dateend', None)
    hidedates=options.get('hidedates')
    hidehours=options.get('hidehours')

    print>>debug, "********************** serving ***********************"

    import trac
    # override timestart if datestart given
    try:
        if datestart: timestart = trac.util.parse_date(datestart)
    except Exception:
        raise Exception, "invalid startdate: '%s', expected format: '%s'" % (str(datestart), trac.util.get_date_format_hint())

    # override timeend if dateend given
    try:
        if dateend: timeend = trac.util.parse_date(dateend)
    except Exception:
        raise Exception, "invalid dateend: '%s', expected format: '%s'" % (str(dateend), trac.util.get_date_format_hint())

    # this dict stores tickets. Tickets are updated on each 'revision' visited - so this is somekinf of snapshot of ticket data at given time
    tickets = {}

    def calc_hours(tickets,max_time):
        """Calculates totalhours of tickets on current tickets state taking filters in the account."""
        result = 0.0
        for ticket in tickets.values():
            if targetmilestone and ticket['milestone'] != targetmilestone: continue
            if targetticket and ticket['ticket'] != targetticket: continue
            if targetcomponent and ticket['component'] != targetcomponent: continue
            result += (ticket['estimate'] - ticket['totalhours'])
        return result

    def tofloat(obj):
        """Converts object to float. Accepts bot dot and comma as decimal separator. If object is None or empty string, 0.0 is returned."""
        if isinstance(obj,float):
            return obj
        if not obj: # None or empty string
            return 0.0
        if isinstance(obj,str) or isinstance(obj,unicode):
            return float(obj.replace(",","."))
        return float(obj) #fallback

    cursor = db.cursor()

    # ----------------------------------------------------
    # fetch the last known state (HEAD revision) of tickets and store to memory
    # ----------------------------------------------------

    # outer join may return zero or '' if there is no such field, so we use arithmetic opration -0.0 to 'cast' result to be valid float value
    sql = """
        SELECT t.id, t.time, t.status, t.milestone, est.value-0.0, th.value-0.0, t.component
        FROM ticket t
            LEFT OUTER JOIN ticket_custom est ON (t.id = est.ticket AND est.name = 'estimatedhours')
            LEFT OUTER JOIN ticket_custom th ON (t.id = th.ticket AND th.name = 'totalhours')
        ORDER BY t.id
        """
    for (ticket,time, status,milestone,estimate,totalhours,component) in cursor.execute(sql).fetchall():
        tickets[ticket] = {'ticket':ticket,
                           'status':status,
                           'milestone':milestone,
                           'estimate':estimate,
                           'totalhours':totalhours,
                           'time':time,
                           'component':component}
        #print>>debug, "ticket #%d: %s" % (ticket, str(tickets[ticket]))


    # ----------------------------------------------------
    # process timestamps from last ticket change/creation
    # to first ticket created and build x/y-pairs to result array
    # ----------------------------------------------------

    result = []
    def process_time(time):
        hours = calc_hours(tickets,time) # todo: remove time from call
        if len(result) >= 2 and result[-1] == hours:
            # update timestamp
            result[-2] = time
        elif len(result) < 2 or result[-1] != hours:
            # data changed from previous item -> write row
            result.append(time)
            result.append(hours)
            

    def process_ticket_create(t, id):
        del tickets[id]

    def process_ticket_change(t, id):
        sql = """
            SELECT ticket, time, field, oldvalue, newvalue
            FROM ticket_change
            WHERE time=%d AND ticket=%d AND field IN('estimatedhours', 'totalhours', 'milestone', 'component') 
            ORDER BY time desc""" % (t,id)
        data = cursor.execute(sql).fetchall()
        # print>>debug, "ticket_change data:"
        #for line in data:
        #    print>>debug, line

        for (ticket,time,field,oldvalue,newvalue) in data:
            # we iterate backwards, thus we save old values
            if field == 'totalhours':
                tickets[ticket]['totalhours'] = tofloat(oldvalue)
            elif field == 'estimatedhours':
                tickets[ticket]['estimatedhours'] = tofloat(oldvalue)
            elif field == 'milestone':
                tickets[ticket]['milestone'] = oldvalue
            elif field == 'component':
                tickets[ticket]['component'] = oldvalue

    # -- find out timestamps (revisions) and bind processors for them

    timestamps = {}
    for line in cursor.execute("SELECT DISTINCT time, id from ticket ORDER BY time").fetchall():
        timestamps[int(line[0])] = [(process_ticket_create, int(line[1]))]

    for line in cursor.execute("SELECT DISTINCT time, ticket from ticket_change ORDER BY time").fetchall():
        item = timestamps.get(int(line[0]),[])
        item.insert(0, (process_ticket_change, int(line[1])))
        timestamps[int(line[0])] = item

    # -- process each timestamp from oldest to newest (direction is importat cos we know only the latest time)

    tmp = [] + timestamps.keys()
    tmp.sort()
    tmp.reverse() # from oldest to youngest
    for t in tmp:
        # print status after changes first (remember backward iterating)
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

    #print>>debug, "result=",str(result)

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

    fx = 100.0 / largesttime
    fy = 100.0 / maxhours

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
        import trac
        # http://www.w3.org/TR/SVG11/text.html#AlignmentProperties
        svg += '<text x="0" y="99%%" text-anchor="start" style="font-family:verdana;">%s</text>' % (trac.util.format_datetime(smallesttime))
        svg += '<text x="100%%" y="99%%" text-anchor="end" style="font-family:verdana;">%s</text>' % (trac.util.format_datetime(smallesttime+largesttime))

    svg += "</svg>\n"
    return svg

if __name__ == "__main__":
    "This is just for testing the stuff from command line"

    def build_svg_paramlist(db, **args):
        return build_svg(args)

    from trac.env import open_environment
    env = open_environment("c:\\scm\\trac\\visualizerdemo")
    db = env.get_db_cnx()
    import sys
    svg = build_svg_paramlist(db, milestone='mile1', time_interval=3600*24, debug=sys.stdout, datestart="8/1/07", dateend="10/1/07")

    FILE = open("c:\\test.svg", "w")
    FILE.write(svg)
    FILE.close()

def process_request(plugin, req):
    """Renders a svg graph based on request attributes and returns a http response (or traceback in case of error)"""
    class MyDebug:
        out = ""
        def write(self, data):
            self.out += data

    import tractimevisualizerplugin
    debug = None;
    if tractimevisualizerplugin.DEVELOPER_MODE:
        debug = MyDebug()
    try:
        from trac.web import RequestDone
        from trac.util.datefmt import http_date
        from time import time

        req.send_response(200)
        req.send_header('Content-Type', "image/svg+xml")
        req.send_header('Last-Modified', http_date(time()))
        req.end_headers()

        if req.method != 'HEAD':
            db = plugin.env.get_db_cnx()
            req.write(build_svg(db, req.args, debug))
        raise RequestDone
    finally:
        if debug:
            plugin.log.debug(debug.out)
