#!python
"""
  p4_trac_jobs.py -- Perforce jobs to/from Trac tickets.
  A simple Synchroniser to update Trac tickets or Perforce jobs.
  Copyright 2006, Thomas Tressieres <thomas.tressieres@calyon.com>

  How to use
  ----------
   * Create a config file:
          trac_project : /data/trac/test # REQUIRED path to Trac environment
          p4_to_trac   :                 # REQUIRED mapping from Perforce to Trac status
            p4_status    : trac_status       # Subsequent lines are p4 to trac mapping
          trac_to_p4   :                 # REQUIRED mapping from Trac to Perforce status
            trac_status  : p4_status         # Subsequent lines are trac to p4 mapping
          debug        : 0               # OPTIONAL (0:no message, 1:some, 2:all)
          p4port       : localhost:1666  # OPTIONAL (by default P4PORT variable)
          p4user       : MyName          # OPTIONAL (by default P4USER variable)
          p4passwd     : MyPassword      # OPTIONAL (by default P4PASSWD variable)
          p4job_prefix : job             # OPTIONAL specify the prefix used to name job in Perforce
          check_delay  : 60              # OPTIONAL interval between checks (60 by default)
          first_check  : -1              # OPTIONAL specify how many history are  -1: all, 0:none
          dry_run      : 1               # OPTIONAL specify if updates are performed in Perfoce/Trac systems

   * default config file is : p4trac.conf

   * Commandline opions:
                  -h | -? | --help
                  -f <config file> | --file=<config file>
"""

import os
import sys
import getopt
import re
import traceback
import time

from trac.core import TracError
from trac.env import Environment
from trac.ticket import Ticket
from trac.web.href import Href
from trac.ticket.notification import TicketNotifyEmail
import perforce


def readConfig(file):
    """
    open the specified file and parse each line to retrive key/value pairs
    empty lines and lines beggining with # are ignored
    """

    OPTRE = re.compile(r'(?P<key>[^:\s][^:]*)' # everything up to :
                       r'\s*[:]\s*'            # any # of space/tab,
                                               # followed by :
                                               # followed by any # space/tab
                       r'(?P<value>.*)$')      # everything up to eol
    SUBOPTRE = re.compile(r'(?P<key>[^:]*)'  # everything up to :
                          r'\s*[:]\s*'       # any # of space/tab,
                                             # followed by :
                                             # followed by any # space/tab
                          r'(?P<value>.*)$') # everything up to eol

    if not os.path.isfile(file):
        print 'File %s does not exist' %file
        sys.exit(1)

    dict = {}
    fp = open(file)
    while True:
        line = fp.readline()
        if not line:
            break
        if line.strip() == '' or line[0] == '#':
            continue

        mo = OPTRE.match(line)
        if mo:
            optname, optval = mo.group('key', 'value')
            optval = optval.strip()
            optname = optname.rstrip().lower()
            try:
                num = int(optval)
                dict[optname] = num
            except ValueError:
                if optval == '':
                    dict[optname] = {}
                else:
                    dict[optname] = optval
        else:
            mo = SUBOPTRE.match(line)
            if mo:
                subname, subval = mo.group('key', 'value')
                subval = subval.strip()
                subname = subname.strip()
                dict[optname][subname] = unicode(subval)

    if 'debug' in dict:
        print dict
    return dict


class PerforceJob(object):
    """A Perforce job implementation
    Built on top of the PyPerforce API.
    http://pyperforce.sourceforge.net/
    """
    def __init__(self, settings):
        """connect to the Perforce server using setting's parameters
        """
        self.job_prefix = settings.get('p4job_prefix', 'job')
        self.job_re = re.compile(r'%s(?P<id>[0-9]+)' %  self.job_prefix)
        self.p4 = perforce.Connection(port=settings['p4port'])
        try:
            self.p4.connect(prog='TracTickets')
            self.p4.user = settings['p4user']
            self.p4.password = settings['p4passwd']
        except (ConnectionFailed, PerforceError), e:
            print str(e)
            raise e

    def __del__(self):
        """disconnect from Perforce server
        """
        self.p4.disconnect()

    def searchTickets(self, nbsec):
        """search tickets updated since nbsec, if nbsec is -1, it checks all jobs
        else check is performed since now - nbsec.
        """
        try:
            if nbsec == -1:
                results = self.p4.run('jobs', '-e', 'job='+self.job_prefix+'*')
            else:
                olddate = time.strftime("%Y/%m/%d:%H:%M:%S", time.localtime(time.time() - nbsec))
                results = self.p4.run('jobs', '-e', 'date>='+olddate+'&job='+self.job_prefix+'*')
        except perforce.PerforceError, e:
            print str(e)
            raise e

        tickets = {}
        for record in results.records:
            r = self._createRecord(record)
            mo = self.job_re.match(record['Job'])
            if mo:
                key = int(mo.group('id'))
                tickets[key] = r
            else:
                print 'error when parsing %s' % record['Job']

        # small bug in pyperforce, the first job is in form result
        for record in results.forms:
            r = self._createRecord(record)
            mo = self.job_re.match(record['Job'])
            if mo:
                key = int(mo.group('id'))
                tickets[key] = r
            else:
                print 'error when parsing %s' % record['Job']
        return tickets

    def searchFixes(self, key):
        """search fixes linked to a job
        """
        try:
            jobname = '%s%06d' % (self.job_prefix, key)
            results = self.p4.run('fixes', '-j', str(jobname))
        except PerforceError, e:
            print str(e)
            raise e

        fixes = []
        for record in results.records:
            fixes.append( record['Change'] )
        return fixes

    def updateTicket(self, id, ticket):
        """update Perforce's job fields from a Trac ticket, the ticket must have
        three fields: Status, User and Description. The job created has a name
        like jobprefixXXXXXX.
        """
        try:
            jobname = '%s%06d' % (self.job_prefix, id)
            job = perforce.Job(self.p4, jobname)

            job['Status'] = settings['trac_to_p4'][ticket['Status']]
            job['Description'] = ticket['Description'].encode('latin-1')
            job['User'] = ticket['User'].encode('latin-1')
            job['Date'] = time.strftime("%Y/%m/%d %H:%M:%S",
                                        time.localtime(ticket['Date']))

            if settings.get('debug', 0):
                print "update Perforce %s  %s" % (jobname, ticket)
            if settings.get('dry_run', 0) == 0:
                job.save(force=True)

        except perforce.PerforceError, e:
            print "Perforce error during update : %s" % (str(e))

    def _createRecord(self, record):
        """internal method used to store Perforce's job description
        """
        mydate = time.mktime(time.strptime(record['Date'], "%Y/%m/%d %H:%M:%S"))
        r = {}
        r['Date'] = int(mydate)
        r['Status'] = record['Status']
        r['Description'] = unicode(record['Description'][:-1], 'latin-1')
        r['User'] = unicode(record['User'], 'latin-1')
        r['From'] = u'p4'
        return r


class TracTicket(object):
    """A Trac ticket implementation
    see http://trac.edgewall.org/
    """

    def __init__(self, env, parameters):
        self.env = env
        self.db = None
        self.get_config = self.env.config.get

    def searchTickets(self, nbsec):
        """search tickets updated since nbsec, if nbsec is -1, it checks all jobs
        else check is performed since now - nbsec.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        tickets = {}
        if nbsec == -1:
            sql = 'SELECT id, changetime, owner, summary, status FROM ticket'
        else:
            sql = 'SELECT id, changetime, owner, summary, status FROM ticket WHERE strftime(\'%s\',  \'now\') - changetime < ' + str(nbsec)
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row == None:
                break
            r = { 'Date' : row[1], 'Status': row[4], 'Description' : row[3],
                  'User':row[2], 'From':u'trac' }
            tickets[row[0]] = r

        return tickets

    def searchFixes(self, id, jobs):
        """try to retrieve comment input string into ticket's changes stored
        in sqlite db.
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        begin_ticket_re = re.compile(r'see changelist')
        ticket_re = re.compile(r'\d+')

        tickets = {}
        sql = 'SELECT newvalue FROM ticket_change where field="comment" and ticket=%d' % (id)
        cursor.execute(sql)
        while True:
            row = cursor.fetchone()
            if row == None:
                break
            row = str(row)
            if begin_ticket_re.search(row):
                trac = set([])
                for x in ticket_re.findall(row):
                    trac.add(int(x))
                jobs.difference_update(trac)

        return jobs

    def updateTicket(self, id, ticket, notification):
        """
        """
        try:
            tkt = Ticket(self.env, id, self.db)
        except TracError, detail:
            print "Cannot create Trac ticket : %s" % (detail)
            return

        tkt['status'] = settings['p4_to_trac'][ticket['Status']]
        if tkt['status'] == u'closed':
            tkt['resolution'] = u'fixed'
        else:
            tkt['resolution'] = u''
        tkt['owner'] = ticket['User']
        tkt['summary'] = ticket['Description']

        jobs = set([])
        comment = ''
        if 'Fixes' in ticket:
            for f in ticket['Fixes']:
                jobs.add(int(f))
            jobs = self.searchFixes(id, jobs)
            if len(jobs) > 0:
                comment = 'see changelist :'
                for j in jobs:
                    comment += ' [%d]' % j
        if settings.get('debug', 0) > 1:
            print "Trac ticket comment %s" % (comment)

        when = ticket['Date']

        if settings.get('debug', 0):
            print "update Trac %d  %s" % (id, ticket)
        if settings.get('dry_run', 0) == 0:
            saved = tkt.save_changes(ticket['User'], comment, when)
            try:
                if saved:
                    self.env.abs_href = Href(self.get_config('project', 'url'))
                    self.env.href = Href(self.get_config('project', 'url'))
                    print self.env.href
                    tn = TicketNotifyEmail(self.env)
                    tn.notify(tkt, False, when)
            except Exception, e:
                print 'TD: Failure sending notification on creation of ticket #%s: %s' %(id, e)

      
class TicketSynchronizer:
    """
    Main class, its job is to check Perforce jobs and Trac tickets at
    regularly intervals.
    if a job or a ticket has been updated since the last check, it has
    to update the other system
    """

    def __init__(self, settings):
        self.env = Environment(settings['trac_project'], create=0)
        self.tkttrac = TracTicket(self.env, settings)
        self.tktperforce = PerforceJob(settings)

    def populate(self, nbsec):
        """main algo to populate the tickets
        """
        self.mergedTickets = self.tkttrac.searchTickets(nbsec)
        perforce = self.tktperforce.searchTickets(nbsec)

        for key in perforce.keys():
            if key in self.mergedTickets: # id is in Trac and Perforce, we have to update only changed fields
                rt = self.mergedTickets[key]
                rp = perforce[key]
                nbRemoved = 0
                if rp['Status'] == settings['trac_to_p4'][rt['Status']]:
                    nbRemoved += 1
                if rp['Description'] == rt['Description']:
                    nbRemoved += 1
                if rp['User'] == rt['User']:
                    nbRemoved += 1

                if rp['Date'] > rt['Date']:
                    fixes = self.tktperforce.searchFixes(key)
                    if len(fixes) != 0:
                        rp['Fixes'] = fixes
                        nbRemoved = 0
                    self.mergedTickets[key] = rp

                if nbRemoved == 3: #if none field was different then we have to suppress entry
                    del self.mergedTickets[key]
            else:
                rp = perforce[key]
                fixes = self.tktperforce.searchFixes(key)
                if len(fixes) != 0:
                    rp['Fixes'] = fixes
                self.mergedTickets[key] = rp

        if settings.get('debug', 0) > 1:
            for p in self.mergedTickets:
                print "key:%06d  value:%s" % (p, self.mergedTickets[p])

    def mainLoop(self):
        delay = settings.get('first_check', -1)
        notify = TicketNotifyEmail(self.env)

        while True:
            self.populate(delay)
            for p in self.mergedTickets:
                if self.mergedTickets[p]['From'] == 'p4':
                    self.tkttrac.updateTicket(p, self.mergedTickets[p], notify)
                if self.mergedTickets[p]['From'] == 'trac':
                    self.tktperforce.updateTicket(p, self.mergedTickets[p])

            delay = settings.get('check_delay', 60)
            time.sleep(delay)


if __name__ == '__main__':
    configfile = 'p4trac.conf'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'h?f:', ['help', 'file='])
    except getopt.error,detail:
        print __doc__
        print detail
        sys.exit(1)

    for opt,value in opts:
        if opt in [ '-h', '--help', '-?']:
            print __doc__
            sys.exit(0)
        elif opt in ['-f', '--file']:
            configfile = value

    settings = readConfig(configfile)
    if not settings.has_key('trac_project'):
        print 'No Trac project is defined in the p4trac config file.'
        sys.exit(1)
    if not settings.has_key('p4_to_trac'):
        print 'No dictionary p4_to_trac is defined in the p4trac config file.'
        sys.exit(1)
    if not settings.has_key('trac_to_p4'):
        print 'No dictionary trac_to_p4 is defined in the p4trac config file.'
        sys.exit(1)

    try:
        ticket = TicketSynchronizer(settings)
        ticket.mainLoop()    

    except Exception, error:
        traceback.print_exc()
