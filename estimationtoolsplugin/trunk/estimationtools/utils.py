from datetime import datetime
from time import strptime
from trac.config import Option
from trac.core import TracError

def get_estimation_field():    
    return Option('estimation-tools', 'estimation_field', 'estimatedhours', 
        doc="""Defines what custom field should be used to calculate estimation charts.
        Defaults to 'estimatedhours'""")

def parse_options(db, options):       
    """Parses the parameters, makes some sanity checks, and creates defaults values
    for missing parameters.    
    """
    cursor = db.cursor()

    # check arguments
    options['milestone'] = options.get('milestone')
    if not options['milestone']:
        raise TracError("No milestone specified!")

    startdatearg = options.get('startdate')
    if startdatearg:
        options['startdate'] = datetime(*strptime(startdatearg, "%Y-%m-%d")[0:5]).date()

    enddatearg = options.get("enddate")
    options['enddate'] = None
    if enddatearg:
        options['enddate'] = datetime(*strptime(enddatearg, "%Y-%m-%d")[0:5]).date()
    if not options['enddate']:            
        # try to get end date from db
        cursor.execute("SELECT completed, due FROM milestone WHERE name = %s", [options['milestone']])
        row = cursor.fetchone()
        if not row:
            raise TracError("Couldn't find milestone %s" % (options['milestone']))
        if row[0]:
            options['enddate'] = datetime.fromtimestamp(row[0]).date()
        elif row[1]:
            options['enddate'] = datetime.fromtimestamp(row[1]).date()
        else:
            options['enddate'] = datetime.now().date()
    todayarg = options.get('today')
    if not todayarg:
        options['today'] = datetime.now().date()
    return options
