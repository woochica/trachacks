#!/opt/trac/0.10.3/install/bin/python

import reporter, slimtimer, users, time_store
import datetime
import trac.env
import logging
import logging.handlers
import os
import sys
import getopt
import time

class ReportDumper:

    def dump(self, trac_base, range_start, range_end):

        #
        # Get the trac environment.
        #
        env = trac.env.open_environment(trac_base)
        if not env:
            print "Couldn't open trac environment at: %s" % trac_base
            return

        #
        # Setup a logger
        #
        log_file = env.config.get('slimtimer', 'report_log')
        if log_file:
            logger = logging.getLogger("ReportDumper")
            if not os.path.exists(os.path.dirname(log_file)):
                print "Couldn't find log file: %s. Aborting. " % log_file
                return
            handler = \
                logging.handlers.RotatingFileHandler(log_file, 'a', 20000, 5)
            formatter = \
                logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        else:
            logger = env.log

        #
        # Check we have some basic stuff for connecting to ST
        #
        st_api_key  = env.config.get('slimtimer', 'api_key')
        if not st_api_key:
            logger.warn("API key for connecting to SlimTimer was not found.")
            return

        #
        # Connect to the database
        #
        db_host     = env.config.get('slimtimer', 'db_host')
        db_username = env.config.get('slimtimer', 'db_username')
        db_password = env.config.get('slimtimer', 'db_password')
        db_dsn      = env.config.get('slimtimer', 'db_dsn')
        missing = []

        if not db_host: missing.append('host')
        if not db_username: missing.append('username')
        if not db_dsn: missing.append('database name')

        if len(missing):
            logger.warn("Missing %s for connecting to the datastore" %
                          ','.join(missing))
            return

        try:
            ts = time_store.TimeStore(host = db_host,
                                      user = db_username,
                                      password = db_password,
                                      database = db_dsn)
        except:
            logger.error("Couldn't connect to database %s (%s@%s)" % 
                           (db_dsn, db_username, db_host))
            return

        #
        # Load the list of users
        #
        users_config_file = os.path.join(trac_base, 'conf', 'users.xml')
        usrs = users.Users(users_config_file)

        #
        # Get the trac db to update
        #
        trac_db = env.get_db_cnx()
        if not trac_db:
            logger.warn("Could not fetch the trac database. "
                        "trac will not be updated.")

        #
        # Iterate through users for whom we should do reporting
        #
        for user in usrs.users.values():
            if user.get('report',False) and user.get('st_user',''):
                st_username = user['st_user']
                st_password = user.get('st_pass','')

                try:
                    st = slimtimer.SlimTimerSession(st_username, st_password,
                                                    st_api_key)
                except:
                    logger.error(
                            "Could not log in to SlimTimer with username %s,"\
                            " password %s character(s) in length, and API "\
                            "key %s." % 
                            (st_username, len(st_password), st_api_key))
                    return None

                rpt = reporter.Reporter(ts, st, usrs, logger, trac_db)
                rpt.fetch_entries(range_start, range_end)

        logger.debug("Dumped records from %s to %s" % (range_start, range_end))

def usage():
    print """Usage:
dump_users --tracbase=<base_path> [range]

Options are:
--tracbase, -b      The absolute path to the base of the trac installation.
                    e.g. /var/trac/0.10.3/var/trac

--rangestart, -s    A date and time specifying the beginning of the range for
                    filtering time entries. This range filters time entry by
                    their START time. Format is YYYY-MM-DD or
                    YYYY-MM-DDTHH:MM:SS. This option may be omitted but noone's
                    quite sure what will happen if you do that.

--rangeempty, -e    A date an time specifying the end of the range of for
                    filtering time entries. Format is YYYY-MM-DD or
                    YYYY-MM-DDTHH:MM:SS. This option may also be omitted at
                    your own risk. Have a nice day.

--days, -d          Set a date range by specifying the number of days in the
                    past to go back. Don't use this with --rangestart and
                    --rangeempty. Who knows what will happen.
        """

def parse_date(date_str):
    #
    # Hey, look over there!
    #
    try:
        return datetime.datetime(*(time.strptime(date_str,
                                    "%Y-%m-%d %H:%M:%S")[0:6]))
    except: pass

    try:
        return datetime.datetime(*(time.strptime(date_str,
                                    "%Y-%m-%dT%H:%M:%S")[0:6]))
    except: pass

    try:
        return datetime.datetime(*(time.strptime(date_str,
                                        "%Y-%m-%d")[0:6]))
    except:
        return None

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "b:s:e:d:", 
                ["tracbase=", "rangestart=", "rangeend=", "days="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    tracbase = ''
    range_start = None
    range_end = None
    ndays = -1

    for opt, arg in opts:
        if opt in ("-b", "--tracbase"):
            tracbase = arg
        elif opt in ("-s", "--rangestart"):
            range_start = parse_date(arg)
        elif opt in ("-e", "--rangeend"):
            range_end = parse_date(arg)
        elif opt in ("-d", "--days"):
            ndays = int(arg)

    if not tracbase:
        usage()
        sys.exit(2)

    if ndays != -1:
        range_end = datetime.datetime.today()
        range_end += datetime.timedelta(days=1)
        range_end -= datetime.timedelta(hours=range_end.hour,
                                        minutes=range_end.minute,
                                        seconds=range_end.second)
        range_start = range_end
        range_start -= datetime.timedelta(days=ndays)

    dumper = ReportDumper()
    dumper.dump(tracbase, range_start, range_end)

if __name__ == '__main__':
    main(sys.argv[1:])

