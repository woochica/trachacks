from datetime import datetime
from trac.util import datefmt

def normalise_datetime(date):
    """Return a timezone aware datetime.datetime object
    
    Sunburnt returns mxDateTime objects in preference to datetime.datetime.
    Sunburnt also doesn't set the timezone info. Trac expects timezone
    aware datetime.datetime objects, so sunburnt dates must be normalised.
    """
    if not date or getattr(date, 'tzinfo', None):
        return date
    try:
        # datetime.datetime
        return date.replace(tzinfo=datefmt.localtz)
    except AttributeError:
        # mxDateTime
        date = datetime.fromtimestamp(date.ticks())
        return date.replace(tzinfo=datefmt.localtz)
