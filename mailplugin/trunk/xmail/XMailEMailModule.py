
import threading
import time
import XMailPermissions

from trac import __version__

from trac.core import * 
from trac.web.api import ITemplateStreamFilter
from trac.notification import SmtpEmailSender, IEmailSender, NotifyEmail,\
    NotificationSystem
from threading import Thread
from trac.util.datefmt import to_datetime, format_datetime, utc
from trac.ticket.api import TicketSystem
from xmail.XMailFilterObject import FilterObject
from trac.loader import get_plugin_info
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.model import Ticket 
from trac.util.translation import domain_functions, get_available_locales,\
    activate
from traceback import print_exc, format_tb
import pkg_resources
from trac.web.main import RequestDispatcher
from trac.util import translation
from trac.prefs.web_ui import Locale
import sys
from trac.util.text import to_unicode
from trac.config import IntOption

_, tag_, N_, add_domain = domain_functions('xmail',  '_', 'tag_', 'N_', 'add_domain')

SEC_MULTIPLIER = 1000000

#===============================================================================
# Module which handels the email notification logic
#===============================================================================
class XMailEventHandler(Component): 
    implements(ITemplateStreamFilter)
 
    """
    Email Modul, required
    """
    _locale_string = 'en'
    
    def __init__(self):
        self.log.debug( "+++++++++++++++ init EMailEventHandler" )
        locale_dir = pkg_resources.resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)
        
    
    def filter_stream(self, req, method, filename, stream, data):
        if not self._TimerIsStillAlive():
            # copied from main.py:310ff
            available = [locale_id.replace('_', '-') for locale_id in
                         translation.get_available_locales()]

            preferred = req.session.get('language', req.languages)
            if not isinstance(preferred, list):
                preferred = [preferred]
            self._locale_string = Locale.negotiate(preferred, available, sep='-')
            self.log.debug("Negotiated locale: %s -> %s",
                           preferred, self._locale_string)
                    
        return stream
        
    #===============================================================================
    # Default Config
    #===============================================================================
    DEFAULT_SLEEP_TIME = IntOption('xmail-plugin', 'sleeptime', 120,
        """Sleep time in seconds for thread. 
        This is the time which determines how often the filter should be checked.""")
    currentTimeInMicroSec = 0
    

    #===========================================================================
    # Controll if the timer thread is still running
    #===========================================================================
    def _TimerIsStillAlive(self):
        threadList = threading.enumerate()
        for threadOb in threadList:
#            if threadOb.__class__.__dict__.has_key('name') and threadOb.name == "xmailThread":
            if threadOb.getName() == "xmailThread":
                if  threadOb.isAlive() == False:
                    self._createXMailThread()
                    self.log.warn('_TimerIsStillAlive: Thread has not been alive; started new Thread')
                    return False
                return True # return since it has already a Thread
        self.log.info("[_TimerIsStillAlive] have not found any thread named 'xmailThread'")
#        self.log.debug('[_TimerIsStillAlive] started Thread')
        self._createXMailThread()
        return False
    
    def _createXMailThread(self):
        myThread = XMailTimerThread(self._sendAllMails, self.DEFAULT_SLEEP_TIME, self.log)
        myThread.setName("xmailThread")
        myThread.start()
    
    def _get_current_time(self):
        return time.time() * SEC_MULTIPLIER

#===============================================================================
# EMail Send Logic
#===============================================================================
    def _sendAllMails(self):
        """Central send logic for sending e-mails"""
        self.log.info( "check mails, language is: %s" % self._locale_string )
        sys_desc = self.get_system_info()
        filterids = self._get_all_relevant_filters()
        
        for filter_id, username in filterids:
            self.log.info ( "[XMail._sendAllMails] -- filter_id: %s -- username: %s" % (filter_id, username) )
            tickets = {}
            subject = "[%s] " % self.env.project_name
            filter = FilterObject(filter_id, db=self.env.get_db_cnx())
            
            # retrieve new tickets
            new_tickets = self._get_relevant_tickets('time', filter)

            # retrieve ticket changes
            changed_tickets = self._get_relevant_tickets('time != changetime and changetime', filter)            
            
            if new_tickets:
                for t in new_tickets:
                    tickets[t['id']] = 'new'
            if changed_tickets:
                for t in changed_tickets:
                    if not tickets.has_key(t['id']):
                        tickets[t['id']] = 'changed'
                    else:
                        changed_tickets.remove(t)
            
            if len(tickets) == 0:
                if filter.values['interval'] > 0:
                    self._set_next_exe(filter, self._get_current_time())
                    self.log.debug("[XMail._sendAllMails] no relevant tickets, since length of tickets is %s" % len(tickets))
                # nothing to do, so continue with next filter
                continue
            
            user_data = self._get_user_data(username)
            self.log.debug( "user data: %r -- negotiated: %s" % (user_data, self._locale_string) )
            if not user_data.has_key('language'):
                self.log.debug("got no user-specific language, so using locale %s" % self._locale_string)
                activate(self._locale_string, self.env.path)
            else:
                activate(user_data['language'], self.env.path)
            
            subject += filter.name
            notifyer = XMailTicketNotify(self.env, {'user_data' : user_data, 
                             'new_tickets': new_tickets,
                             'changed_tickets': changed_tickets,
                             'filter': filter,
                             'sys_desc': sys_desc})
            notifyer.notify(resid=None, subject=subject)
            self._set_next_exe(filter, self._get_current_time())
            self.log.info( "[XMail._sendAllMails] -----> sent email with %r tickets by XMailTicketNotify" % len(tickets) )
        return
    
    def get_system_info(self):
        trac_ver = 'xmail'
        try:
            # get trac-version
            info = self.env.get_systeminfo()
            val = info[0][1]
            if type(val) != list:
                trac_ver = "Trac %s" % (val)
            
            # get xmail-version
            plugins = get_plugin_info(self.env)
            xmail_ver = 'XMail'
            for plugin in plugins:
                if plugin['name'] == "xmailplugin":
                    xmail_ver = "%s %s" % (xmail_ver, plugin['version'])
            trac_ver = "%s (%s)" % (xmail_ver, trac_ver)
        except Exception, e:
            print "error when getting trac_ver: %s" % e
        return trac_ver


#===============================================================================
# DB Access logic
#===============================================================================
    #===========================================================================
    # Returns all filterids and filternaems, which have to been processed 
    # in this cycle
    #===========================================================================
    def _get_all_relevant_filters(self):
        sqlQuery = ( "select id, username from xmail" \
                    " where nextexe <= %s and active is not null"
                    % self._get_current_time() )
        self.log.debug( "_get_all_relevant_filters: sqlQuery: %s" % sqlQuery )
        
        filterIds = self._execute_SQL_Query_and_Feedback(True, sqlQuery)
        if isinstance(filterIds,list):
            return filterIds
        else:
            return []
    
    def _get_relevant_tickets(self, timefilter, filter):
        """retrieve relevant tickets for filterId
        timefilter is usually 'time' (for new tickets) or 'time != changetime and changetime' (for ticket changes) 
        """
        if filter.values['interval'] > 0:
            t = filter.values['nextexe'] - (filter.values['interval'] * 1000000)
        else:
            t = filter.values['lastsuccessexe'] or filter.values['nextexe']
        
        sql = filter.get_filter_select( additional_where_clause="%s>=%s" % 
                                                  (timefilter, t) )
        self.log.debug('_get_relevant_tickets -- sql: %s' % sql)
        
        data = None
        try:
            db = self.env.get_db_cnx()
            myCursor = db.cursor()
            result = []
#            data_dict = {}
            try:
                myCursor.execute(sql)
                data = list(myCursor.fetchall())
            except Exception, e:
                self.log.error("error while fetching data: %s" % e) 
            
#            print "data: %r" % data
            for row in data:
                data_dict = {}
#                print "row: %r" % row
                for i, col in enumerate(row):
                    if i == 0:
                        data_dict['id'] = col
                    else:
                        data_dict[filter.select_fields[i-1]] = col
                result.append(data_dict)
#            print "result: %r" % result
        except Exception, e:
            self.log.info( "could not get relevant ticket, since error occured: %s\n sql: %s" % (e, sql) )

        return result

    
    #===========================================================================
    # Returns the corresponding email-address to the given username
    #===========================================================================
    def _get_user_data(self, username):
        sql = ("select name, value from session_attribute where name in ('language', 'email')"
               " and sid='%s'" % username)
        db = self.env.get_db_cnx()
        myCursor = db.cursor()
        result = None
        try:
            myCursor.execute(sql)
            data = list( myCursor.fetchall() )
            result = {}
            for row in data:
                result[row[0]] = row[1]
        except Exception, e:
            self.log.debug( "e: %s" % e ) # TODO[fm]: remove in prod-mode 
        return result
    
    #===========================================================================
    # 
    #===========================================================================
    def _set_next_exe(self, filter, current_time):
        next_exe = current_time
        if filter.values['interval'] > 0:
            next_exe = (filter.values['interval'] * SEC_MULTIPLIER) + filter.values['nextexe']
            
        sql = "update xmail set nextexe=%i, lastsuccessexe=%i where id=%i" % (next_exe, current_time, filter.id)
        self.log.debug("[_set_next_exe] sql: %s" % sql)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        try:
            cursor.execute(sql)
            db.commit()
            return True
        except Exception, e:
            self.log.error('updating failed, because of error: %s' % e)
            
        return False
        
    #===========================================================================
    # Executes given sql statement and returns the sql result
    #===========================================================================
    def _execute_SQL_Query_and_Feedback(self, select, sqlQuery, *params):

        if sqlQuery != None and params != None:
            db = self.env.get_db_cnx()
            myCursor = db.cursor()
            data = {}
            try:
                myCursor.execute(sqlQuery, params)
                if(select == True):
                    """ result is an 2-dimensinal array of the select results"""
                    data = list(myCursor.fetchall())
                else:
                    """ Result is the amount of insered rows"""
                    data = myCursor.rowcount
                db.commit()
            except Exception, e:
                self.log.error ("Error executing SQL Statement \n ( %s ) \n %s" % (sqlQuery, e))
                db.rollback();
            try:
                db.close()
            except e:
                self.log.error("DB close fails. \n %s" % e)
            return data       

    
class XMailTicketNotify(NotifyEmail):
    _data = None
#    _locale_string = 'en'
    _email_adr = None
    template_name = "timed_email.txt"
    COLS = 75
    COL_DESC = 20
    
    def __init__(self, env, data, template_name=None):
        NotifyEmail.__init__(self, env)
        locale_dir = pkg_resources.resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)
        
        if template_name:
            self.template_name = template_name
        self._data = data
        if self._data and self._data['user_data']:
#            self._locale_string = self._data['user_data']['language'] # not used at the moment
            self._email_adr = self._data['user_data']['email']
#        print "[XMailMultiTicketNotify] self._data: %r --- data: %r --- tickets: %r" % (self._data, data, data['new_tickets'])
    
    # override from TicketNotifyEmail
    def get_recipients(self, tktid):
        ccrecipients = []
        torecipients = []
        
        if self._email_adr:
            torecipients.append(self._email_adr)
        filter_sep = ('=' * self.COLS)
        filter = self._data['filter']
        
        # format objects
        self.data['new_tickets_count'] = len(self._data['new_tickets'])
        self.data['new_tickets'] = self._format_tickets(self._data['new_tickets'])
        self.data['changed_tickets_count'] = len(self._data['changed_tickets'])
        self.data['changed_tickets'] = self._format_tickets(self._data['changed_tickets'])
        self.data['filter_sep'] = filter_sep
        self.data['new_ticket_hdr'] = _('New tickets:')
        self.data['changed_ticket_hdr'] = _('Changed tickets:')
        # simply copy some data objects
        self.data['filter'] = filter
        self.data['sys_desc'] = self._data['sys_desc']
        link = "%s/xmail/xmail-edit.html?id=%i" % (self.env.abs_href.base, filter.id)
        self.data['change_hint'] = tag_('To change the filter go to %(link)s', link=link)
        
#        return ([], [])
        return (torecipients, ccrecipients)
    
    def _format_tickets(self, tickets):
        if not tickets or not type(tickets) in (list, tuple):
            return None
        
        sep = ('-' * self.COLS) + '\n'
        href = self.env.abs_href.base
        format = "%%%is: %%s\n" % self.COL_DESC
        txt = None
        
        for ticket in tickets:
            id = ticket['id']
            summary = ticket['summary']
            big_cols = []
            time_fld = ""
            
            if not txt:
                txt = "#%s" % id
            else:
                txt += "\n\n#%s" % id
                
            if summary:
                txt += ": %s" % summary
            txt += "\n%s/ticket/%s\n" % (href, id) # add link
            txt += sep
            for key in ticket.keys():
                if key in ('time', 'changetime'):
                    time_fld += format % (_(key), format_datetime(ticket[key]))
                elif not key in ('id', 'summary'):
                    content = ticket[key]
                    if not content: continue # ignore empty fields
                    elif type(tickets) == str and len(content) > (self.COLS - self.COL_DESC):
                        big_cols.append({key: ticket[key]})
                    else:
                        txt += format % (_(key), content)
            txt += time_fld
            
            for bg in big_cols:
                for key in bg: # should only be key = value
                    txt += "%s:\n%s" % (_(key), bg[key])
                
        return txt
        
    
#===============================================================================
# Timer Implementation
#===============================================================================
#===========================================================================
# Timer Implementation with execute a given function in an given intervall
# @param func: Function to call
# @param sec: Sleep intervall in seconds
#===========================================================================
class XMailTimerThread(Thread):
    def __init__(self, func, sec=30, log_func=None):
        Thread.__init__(self)
        self.func = func
        self.sec = sec
        self.log = log_func
        if self.log:
            self.log.info('XMailTimerThread: init done with sec: %s' % sec)

    def run(self):
        while True:
            try:
                # error occured: 'ascii' codec can't encode character u'\xfc' in position 19: ordinal not in range(128)
                self.func()
            except Exception, e:
                if self.log:
                    self.log.error('==============================\n' \
                                   '[XMailTimerThread.run] -- Exception occured: %r' % e)
                    exc_traceback = sys.exc_info()[2]
                    self.log.error('TraceBack: %s' % format_tb(exc_traceback) )

            if self.log:
                self.log.debug('sleeping %s secs' % self.sec)
            time.sleep(self.sec)
            