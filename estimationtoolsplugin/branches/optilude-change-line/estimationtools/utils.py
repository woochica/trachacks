from datetime import datetime
from time import strptime
from trac.config import Option, ListOption
from trac.core import TracError
from trac.wiki.api import parse_args
from trac.ticket.query import Query

AVAILABLE_OPTIONS = ['startdate', 'enddate', 'today', 'width', 'height', 'color', 'title', 'change', 'interval_days']

def get_estimation_field():    
    return Option('estimation-tools', 'estimation_field', 'estimatedhours', 
        doc="""Defines what custom field should be used to calculate estimation charts.
        Defaults to 'estimatedhours'""")

def get_initial_estimation_field():    
    return Option('estimation-tools', 'initial_estimation_field', '', 
        doc="""When calculating project change, use this field instead of the one set for estimation_field.
        Defaults to be the same as 'estimation_field'""")

def get_closed_states():
    return ListOption('estimation-tools', 'closed_states', 'closed', 
        doc="""Set to a comma separated list of workflow states that count as "closed", 
        where the effort will be treated as zero, e.g. closed_states=closed,another_state. 
        Defaults to closed.""")
    
def get_estimation_suffix():
    return Option('estimation-tools', 'estimation_suffix', 'h',
        doc="""Suffix used for estimations. Defaults to 'h'""")

def parse_options(db, content, options):       
    """Parses the parameters, makes some sanity checks, and creates default values
    for missing parameters.    
    """
    cursor = db.cursor()

    # check arguments
    _, parsed_options = parse_args(content, strict=False)
    
    options.update(parsed_options)

    startdatearg = options.get('startdate')
    if startdatearg:
        options['startdate'] = datetime(*strptime(startdatearg, "%Y-%m-%d")[0:5]).date()

    enddatearg = options.get("enddate")
    options['enddate'] = None
    if enddatearg:
        options['enddate'] = datetime(*strptime(enddatearg, "%Y-%m-%d")[0:5]).date()

    if not options['enddate'] and options.get('milestone'):   
        # use first milestone
        milestone = options['milestone'].split('|')[0]         
        # try to get end date from db
        cursor.execute("SELECT completed, due FROM milestone WHERE name = %s", [milestone])
        row = cursor.fetchone()
        if not row:
            raise TracError("Couldn't find milestone %s" % (milestone))
        if row[0]:
            options['enddate'] = datetime.fromtimestamp(row[0]).date()
        elif row[1]:
            options['enddate'] = datetime.fromtimestamp(row[1]).date()

    if not options['enddate']:
            options['enddate'] = datetime.now().date()
    todayarg = options.get('today')
    if not todayarg:
        options['today'] = datetime.now().date()
    
    if 'interval_days' in options:
        try:
            options['interval_days'] = int(options['interval_days'])
        except (ValueError, TypeError):
            options['interval_days'] = 1
    else:
        options['interval_days'] = 1
        
    if 'change' in options and options['change'].lower() not in ('false', '0'):
        options['change'] = True
    else:
        options['change'] = False
    
    # all arguments that are no key should be treated as part of the query  
    query_args = {}
    for key in options.keys():
        if not key in AVAILABLE_OPTIONS:
            query_args[key] = options[key]
    return options, query_args

def execute_query(env, req, query_args):
    query_string = '&'.join(['%s=%s' % item for item in query_args.iteritems()])
    query = Query.from_string(env, query_string)

    tickets = query.execute(req)

    tickets = [t for t in tickets 
               if ('TICKET_VIEW' or 'TICKET_VIEW_CC') in req.perm('ticket', t['id'])]
    
    return tickets

