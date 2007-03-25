import time

def to_timestamp(datetime):
    """ Convert xmlrpclib.DateTime string representation to UNIX timestamp. """
    return time.mktime(time.strptime('%s UTC' % datetime.value, '%Y%m%dT%H:%M:%S %Z')) - time.timezone
