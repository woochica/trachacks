# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''

###############################################################################
##
##        C O R E    C L A S S E S     O F     T H E    P L U G I N 
##
###############################################################################

from datetime import datetime, timedelta
from time import  time, localtime
from threading import Timer



from trac.core import Component, ExtensionPoint, implements
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import IRequestHandler
from trac.web.chrome import add_notice, add_warning, add_link
from trac.util.translation import _
from trac.util.text import exception_to_unicode
from trac.util.datefmt import utc, http_date

from traccron.api import ICronTask, IHistoryTaskExecutionStore, ISchedulerType, ITaskEventListener


class Core(Component):    
    """
    Main class of the Trac Cron Plugin. This is the entry point
    for Trac plugin architecture
    """    
    
    implements(IAdminPanelProvider, ITemplateProvider, IRequestHandler)
    
    cron_tack_list = ExtensionPoint(ICronTask)
    
    supported_schedule_type = ExtensionPoint(ISchedulerType)
    
    task_event_list = ExtensionPoint(ITaskEventListener)    
    
    history_store_list = ExtensionPoint(IHistoryTaskExecutionStore)

    current_ticker = None
    
    def __init__(self,*args,**kwargs):
        """
        Intercept the instanciation to start the ticker
        """        
        Component.__init__(self, *args, **kwargs)
        self.cronconf = CronConfig(self.env)        
        self.webUi = WebUi(self)        
        self.apply_config()        

        
    def apply_config(self, wait=False):
        """
        Read configuration and apply it
        """
        # stop existing ticker if any
        self.env.log.debug("applying config")
        if Core.current_ticker is not None:
            self.env.log.debug("stop existing ticker")
            Core.current_ticker.cancel(wait=wait)

        if self.getCronConf().get_ticker_enabled():
            self.env.log.debug("ticker is enabled")
            # try to execute task a first time
            # because we don't want to wait for interval to elapse
            self.check_task()
            Core.current_ticker = Ticker(self.env,self.getCronConf().get_ticker_interval(), self.check_task)
        else:
            self.env.log.debug("ticker is disabled")
            

    def getCronConf(self):
        """
        Return the configuration for TracCronPlugin
        """
        return self.cronconf
    
    def getTaskList(self):
        """
        Return the list of existing task
        """
        return self.cron_tack_list
    
    def getSupportedScheduleType(self):
        """
        Return the list of supported schedule type
        """
        return self.supported_schedule_type
    
    
    def getHistoryList(self):
        """
        Return the list of history store
        """
        return self.history_store_list
    
    def getTaskListnerList(self):
        """
        Return the list of task event listener
        """
        return self.task_event_list
    
    def clearHistory(self):
        """
        Clear history store
        """
        for history in self.history_store_list:
            history.clear()
    
    def check_task(self):
        """
        Check if any task need to be executed. This method is called by the Ticker.
        """
        # store current time
        currentTime = localtime(time())
        self.env.log.debug("check existing task");
        for task in self.cron_tack_list:
            if self.cronconf.is_task_enabled(task):                
                # test current time with task planing
                self.env.log.debug("check task " + task.getId())
                for schedule in self.supported_schedule_type:
                    if self.cronconf.is_schedule_enabled(task, schedule=schedule):
                        # run task if needed
                        if schedule.isTriggerTime(task, currentTime):
                            self._runTask(task, schedule)
                        else:
                            self.env.log.debug("nothing to do for " + task.getId());
                    else:
                        self.env.log.debug("schedule " + schedule.getId() + " is disabled")
            else:
                self.env.log.debug("task " + task.getId() + " is disabled")


    def runTask(self, task, parameters=None):
        '''
        run a given task with specified argument string
        parameters maybe comma-separated values
        '''
        self._runTask(task, parameters=parameters)
        
    # IAdminPanel interface
    
    def get_admin_panels(self, req):
        return self.webUi.get_admin_panels(req)


    def render_admin_panel(self, req, category, page, path_info):
        return self.webUi.render_admin_panel(req, category, page, path_info)

    # ITemplateProvider interface
    
    def get_htdocs_dirs(self):
        return self.webUi.get_htdocs_dirs()


    def get_templates_dirs(self):
        return self.webUi.get_templates_dirs()
    
    # IRequestHandler interface
    
    def match_request(self, req):
        return self.webUi.match_request(req)

    def process_request(self, req): 
        return self.webUi.process_request(req)
    
    # internal method
  
    def _notify_start_task(self, task):
        for listener in self.task_event_list:
            # notify only if listener is enabled
            if self.cronconf.is_task_listener_enabled(listener):
                try:    
                    listener.onStartTask(task)
                except Exception, e:
                    self.env.log.warn("listener %s failed  onStartTask event : %s" % (str(listener),exception_to_unicode(e)))                                    


    def _notify_end_task(self, task, success=True):
        for listener in self.task_event_list:
            if self.cronconf.is_task_listener_enabled(listener):
                try:
                    listener.onEndTask(task, success)
                except Exception, e:
                    self.env.log.warn("listener %s failed  onEndTask event : %s" % (str(listener),exception_to_unicode(e)))

    def _runTask(self, task, schedule=None, parameters=None):
        self.env.log.info("executing task " + task.getId()) # notify listener
        self._notify_start_task(task)
        try:
            args = []
            if schedule : 
                args = self.cronconf.get_schedule_arg_list(task, schedule)
            elif parameters:
                args = parameters
            task.wake_up(*args)
        except Exception as e:
            self.env.log.error('task execution result : FAILURE %s', exception_to_unicode(e))
            self._notify_end_task(task, success=False)
        else:
            self.env.log.info("task execution result : SUCCESS")
            self._notify_end_task(task)
            self.env.log.info("task " + task.getId() + " finished")





class Ticker():
    """
    A Ticker is simply a simply timer that will repeatly wake up.
    """
    
    
    def __init__(self, env, interval, callback):
        """
        Create a new Ticker.
        env : the trac environnement
        interval: interval in minute
        callback: the function callback to call o every wake-up
        """
        self.env = env
        self.interval = interval
        self.callback = callback
        self.timer = None
        self.create_new_timer()
        
    def create_new_timer(self, wait=False, delay=None):
        """
        Create a new timer before killing existing one if required.
        wait : if True the current thread wait until running task finished. Default is False
        """
        self.env.log.debug("create new ticker")
        if (self.timer != None):
            self.timer.cancel()
            if ( wait ):
                self.timer.join()            
        
        if delay:
            # use specified delay to wait
            _delay = delay
        else:
            # use default delay
            _delay = self.interval * 60 
        self.timer = Timer( _delay, self.wake_up)
        self.timer.start()
        self.env.log.debug("new ticker started")

    def wake_up(self):
        '''
        Wake up this ticker. This ticker will call the callback function then
        create a new timer to wake it up again
        '''
        self.env.log.debug("ticker wake up")
        in_hurry = True
        while (in_hurry):
            wake_up_time = datetime(*datetime.now().timetuple()[:6])
        
            self.callback()
            
            now = datetime(*datetime.now().timetuple()[:6])
            next_wake_up_time = wake_up_time + timedelta(minutes=self.interval)            
            self.env.log.debug("last wake up time %s" % str(wake_up_time))
            self.env.log.debug("next wake up time %s" % str(next_wake_up_time))
            self.env.log.debug("current time %s" % str(now))

            if  now < next_wake_up_time:  
                # calculate amount of second to wait in second
                seconds_before_next_wake_up = (next_wake_up_time - now).seconds
                # need to adjust it to ensure to skip this last wake up  minute window                            
                if next_wake_up_time.second == 0 :
                    # slide up 1 second  
                    seconds_before_next_wake_up += 1
                # need to adjust it to ensure to not skip next minute window
                elif next_wake_up_time.second == 59:
                    # slid down 1 second 
                    seconds_before_next_wake_up -= 1
                    
                self.env.log.debug("adjusted wait %s secondes" % seconds_before_next_wake_up)
                self.create_new_timer(delay=seconds_before_next_wake_up)
                in_hurry = False
            else :
                # the next wake up is over,
                seconds_before_next_wake_up = (now - next_wake_up_time).seconds
                self.env.log.warn("task processing duration overtake ticker interval\n"
                                  "next wake up is over since %d seconds " % seconds_before_next_wake_up) 
        
    
    def cancel(self, wait=False):
        self.timer.cancel()
        if (wait):
            self.timer.join()

        
 
class CronConfig():
    """
    This class read and write configuration for TracCronPlugin
    """
    
    TRACCRON_SECTION = "traccron"
    
    TICKER_ENABLED_KEY = "ticker_enabled"
    TICKER_ENABLED_DEFAULT = "False"
    
    TICKER_INTERVAL_KEY = "ticker_interval"
    TICKER_INTERVAL_DEFAULT = 1 #minutes
    
    TASK_ENABLED_KEY = "enabled"
    TASK_ENABLED_DEFAULT = "True"
    
    SCHEDULE_ENABLED_KEY = "enabled"
    SCHEDULE_ENABLED_DEFAULT = "True"

    SCHEDULE_ARGUMENT_KEY ="arg"
    SCHEDULE_ARGUMENT_DEFAULT = ""
    
    TASK_LISTENER_ENABLED_KEY = "enabled"
    TASK_LISTENER_ENABLED_DEFAULT = "True"    
    
    EMAIL_NOTIFIER_TASK_BASEKEY = "email_task_event"
    
    EMAIL_NOTIFIER_TASK_LIMIT_KEY = "limit"
    EMAIL_NOTIFIER_TASK_LIMIT_DEFAULT = 1
    
    EMAIL_NOTIFIER_TASK_RECIPIENT_KEY = "recipient"
    EMAIL_NOTIFIER_TASK_RECIPIENT_DEFAULT = ""
    
    EMAIL_NOTIFIER_TASK_ONLY_ERROR_KEY = "only_error"
    EMAIL_NOTIFIER_TASK_ONLY_ERROR_DEFAULT = "False"
    
    UNREACHABLE_MILESTONE_TASK_BASEKEY="unreachable_milestone"
    UNREACHABLE_MILESTONE_TASK_RECIPIENT_KEY = "recipient"
    UNREACHABLE_MILESTONE_TASK_RECIPIENT_DEFAULT = ""
    

    def __init__(self, env):
        self.env = env
            
    def get_ticker_enabled(self):
        return self.env.config.getbool(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, self.TICKER_ENABLED_DEFAULT)

    def set_ticker_enabled(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.TICKER_ENABLED_KEY, value)
    
    def get_ticker_interval(self):
        return self.env.config.getint(self.TRACCRON_SECTION, self.TICKER_INTERVAL_KEY, self.TICKER_INTERVAL_DEFAULT)
    
    def set_ticker_interval(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.TICKER_INTERVAL_KEY, value)
    
    def get_schedule_value(self, task, schedule_type):
        """
        Return the raw value of the schedule
        """
        return  self.env.config.get(self.TRACCRON_SECTION,task.getId() + "." + schedule_type.getId(), None)

    def get_schedule_value_list(self, task, schedule_type):
        """
        Return the list of value for the schedule type and task
        """
        return  self.env.config.getlist(self.TRACCRON_SECTION,task.getId() + "." + schedule_type.getId())

    def set_schedule_value(self, task, schedule_type, value):
        self.env.config.set(self.TRACCRON_SECTION, task.getId() + "." + schedule_type.getId(), value)
    
    def is_task_enabled(self, task):
        """
        Return the value that indicate if the task is enabled
        """
        return self.env.config.getbool(self.TRACCRON_SECTION, task.getId() + "." + self.TASK_ENABLED_KEY, self.TASK_ENABLED_DEFAULT)

    def set_task_enabled(self, task, value):
        self.env.config.set(self.TRACCRON_SECTION, task.getId() + "." + self.TASK_ENABLED_KEY, value)
    
    def is_schedule_enabled(self, task, schedule):
        """
        Return the value that indicate if the schedule for a given task is enabled
        """
        return self.env.config.getbool(self.TRACCRON_SECTION, task.getId() + "." + schedule.getId() + "." +  self.SCHEDULE_ENABLED_KEY, self.SCHEDULE_ENABLED_DEFAULT)

    def set_schedule_enabled(self, task, schedule, value):
        self.env.config.set(self.TRACCRON_SECTION, task.getId() + "." + schedule.getId() + "." + self.SCHEDULE_ENABLED_KEY, value)
    
    def get_schedule_arg(self, task, schedule):
        """
        Return the raw value of argument for a given schedule of a task
        """
        return self.env.config.get(self.TRACCRON_SECTION, task.getId() + "." + schedule.getId() + "." + self.SCHEDULE_ARGUMENT_KEY, None)
 

    def get_schedule_arg_list(self, task, schedule):
        """
        Return the list of argument for a given schedule of a task
        """
        return self.env.config.getlist(self.TRACCRON_SECTION, task.getId() + "." + schedule.getId() + "." + self.SCHEDULE_ARGUMENT_KEY)
    
    def set_schedule_arg(self, task, schedule, value):
        self.env.config.set(self.TRACCRON_SECTION, task.getId() + "." + schedule.getId() + "." + self.SCHEDULE_ARGUMENT_KEY, value)
    
  
    def get_email_notifier_task_limit(self):
        """
        Return the number of task event to notify.
        """
        return self.env.config.getint(self.TRACCRON_SECTION, 
                                      self.EMAIL_NOTIFIER_TASK_BASEKEY + "." +  self.EMAIL_NOTIFIER_TASK_LIMIT_KEY, self.EMAIL_NOTIFIER_TASK_LIMIT_DEFAULT)
    
    def get_email_notifier_task_recipient(self):
        """
        Return the recipients for task listener as raw value
        """
        return self.env.config.get(self.TRACCRON_SECTION,
                                   self.EMAIL_NOTIFIER_TASK_BASEKEY + "." +  self.EMAIL_NOTIFIER_TASK_RECIPIENT_KEY, self.EMAIL_NOTIFIER_TASK_RECIPIENT_DEFAULT)
    
    def get_email_notifier_task_recipient_list(self):
        """
        Return the recipients for task listener
        """
        return self.env.config.getlist(self.TRACCRON_SECTION,
                                       self.EMAIL_NOTIFIER_TASK_BASEKEY + "." +  self.EMAIL_NOTIFIER_TASK_RECIPIENT_KEY)

    def is_email_notifier_only_error(self):
        """
        Return the value that indicate of the notification must be sent only 
        for task on error
        """
        return self.env.config.getbool(self.TRACCRON_SECTION,
                                       self.EMAIL_NOTIFIER_TASK_BASEKEY + "."  + self.EMAIL_NOTIFIER_TASK_ONLY_ERROR_KEY,
                                       self.EMAIL_NOTIFIER_TASK_ONLY_ERROR_DEFAULT)
    
    def set_email_notifier_only_error(self, value):
        self.env.config.set(self.TRACCRON_SECTION, self.EMAIL_NOTIFIER_TASK_BASEKEY + "." + self.EMAIL_NOTIFIER_TASK_ONLY_ERROR_KEY, value)
    
    def is_task_listener_enabled(self, listener):
        return self.env.config.getbool(self.TRACCRON_SECTION, listener.getId() + "." + self.TASK_LISTENER_ENABLED_KEY, self.TASK_LISTENER_ENABLED_DEFAULT)
    
    def set_task_listener_enabled(self, listener, value):
        self.env.config.set(self.TRACCRON_SECTION, listener.getId() + "." + self.TASK_LISTENER_ENABLED_KEY, value) 


    def get_unreachable_milestone_task_recipient_list(self):
        """
        Return recipient list for unreachable milestone
        """
        return self.env.config.getlist(self.TRACCRON_SECTION,
                                       self.UNREACHABLE_MILESTONE_TASK_BASEKEY + "." + self.UNREACHABLE_MILESTONE_TASK_RECIPIENT_KEY)

    def get_unreachable_milestone_task_recipient(self):
        """
        Return raw value of unreachable milestone recipient
        """    
        return self.env.config.get(self.TRACCRON_SECTION,
                                   self.UNREACHABLE_MILESTONE_TASK_BASEKEY + "." + self.UNREACHABLE_MILESTONE_TASK_RECIPIENT_KEY,
                                   self.UNREACHABLE_MILESTONE_TASK_RECIPIENT_DEFAULT)
    
    def set_value(self, key, value):
        self.env.config.set(self.TRACCRON_SECTION, key, value)
    
    def remove_value(self, key):
        self.env.config.remove(self.TRACCRON_SECTION, key)
    
    def save(self):
        self.env.config.save()

class WebUi(IAdminPanelProvider, ITemplateProvider, IRequestHandler):
    """
    Class that deal with Web stuff. It is the both the controller and the page builder.
    """

    def __init__(self, core):        
        self.env = core.env
        self.cron_task_list = core.getTaskList()        
        self.cronconf = core.getCronConf()
        self.history_store_list = core.getHistoryList()
        self.all_schedule_type = core.getSupportedScheduleType()
        self.cron_listener_list = core.getTaskListnerList()        
        self.core = core
        
    # IAdminPanelProvider
    
    def get_admin_panels(self, req):
        if ('TRAC_ADMIN' in req.perm) :
            yield ('traccron', 'Trac Cron', 'cron_admin', u'Settings')
            yield ('traccron', 'Trac Cron', 'cron_history', u'History')
            yield ('traccron', 'Trac Cron','cron_listener', u'Listener')
          


    def render_admin_panel(self, req, category, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')                
        
        if req.method == 'POST':
            if 'save' in req.args:     
                if page == 'cron_admin':                     
                    self._saveSettings(req, category, page)
                elif page == 'cron_listener':
                    self._saveListenerSettings(req, category, page)   
            elif 'clear' in req.args:
                if page == 'cron_history':
                    self._clearHistory(req, category, page)                 
        else:             
            # which view to display ?
            if page == 'cron_admin':                
                return self._displaySettingView()
            elif page == 'cron_history':
                return self._displayHistoryView(req)
            elif page == 'cron_listener':
                return self._displayListenerView()
                

    # ITemplateProvider

    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestHandler interface
    
    def match_request(self, req):
        return req.path_info.startswith('/traccron/')
        
    def process_request(self, req): 
        if req.path_info == '/traccron/runtask':
            self._runtask(req)
        elif  req.path_info == '/traccron/cron_history': 
            return self._displayHistoryView(req)
        else:
            self.env.log.warn("Trac Cron Plugin was unable to handle %s" % req.path_info)
            add_warning(req, "The request was not handled by trac cron plugin")
            req.redirect(req.href.admin('traccron','cron_admin'))
            

    # internal method    

    def _create_history_list(self):
        """
        Create list of task execution history
        """
        _history = []        
        
        for store in self.history_store_list:
            for task, start, end, success in store.getExecution():
                startTime  = localtime(start)
                endTime  = localtime(end)         
                date = datetime.fromtimestamp(start, utc)
                execution = {
                                 "timestamp": start,
                                 "datetime": date ,
                                 "dateuid" : self._to_utimestamp(date),
                                 "date": "%d-%d-%d" % (startTime.tm_mon, startTime.tm_mday, startTime.tm_year),
                                 "task":task.getId(),
                                 "start": "%02d h %02d" % (startTime.tm_hour, startTime.tm_min),
                                 "end": "%02d h %02d" % (endTime.tm_hour, endTime.tm_min),
                                 "success": success                                 
                                 }       
                _history.append(execution)

        #apply sorting
        _history.sort(None, lambda(x):x["timestamp"])
        return _history
    
    _epoc = datetime(1970, 1, 1, tzinfo=utc)
    
    def _to_utimestamp(self, dt):
        """Return a microsecond POSIX timestamp for the given `datetime`."""
        if not dt:
            return 0
        diff = dt - self._epoc
        return (diff.days * 86400000000L + diff.seconds * 1000000
                + diff.microseconds)

    def _save_config(self, req, notices=None):
        """Try to save the config, and display either a success notice or a
        failure warning.
        """
        try:            

            self.cronconf.save()

            if notices is None:
                notices = [_('Your changes have been saved.')]
            for notice in notices:
                add_notice(req, notice)
        except Exception, e:
            self.env.log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
            add_warning(req, _('Error writing to trac.ini, make sure it is '
                               'writable by the web server. Your changes have '
                               'not been saved.'))

    def _displaySettingView(self, data= {}):
        data.update({self.cronconf.TICKER_ENABLED_KEY:self.cronconf.get_ticker_enabled(), self.cronconf.TICKER_INTERVAL_KEY:self.cronconf.get_ticker_interval()})
        task_list = []
        for task in self.cron_task_list:
            task_data = {}
            task_data['enabled'] = self.cronconf.is_task_enabled(task)
            task_data['id'] = task.getId()
            task_data['description'] = task.getDescription()
            all_schedule_value = {}
            for schedule in self.all_schedule_type:
                value = self.cronconf.get_schedule_value(task, schedule)
                if value is None:
                    value = ""
                task_enabled = self.cronconf.is_schedule_enabled(task, schedule)
                task_arg = self.cronconf.get_schedule_arg(task, schedule)
                if task_arg is None:
                    task_arg = ""
                all_schedule_value[schedule.getId()] = {
                    "value":value, 
                    "hint":schedule.getHint(), 
                    "enabled":task_enabled, 
                    "arg":task_arg}
            
            task_data['schedule_list'] = all_schedule_value
            task_list.append(task_data)
        
        data['task_list'] = task_list      
        return 'cron_admin.html', data
    
    def _displayHistoryView(self, req, data={}):
        # create history list
        data['history_list'] = self._create_history_list()
        
        format = req.args.get('format')
        if ( format == 'rss'):
            return 'cron_history.rss', data,'application/rss+xml'
        else:
            rss_href = req.href.traccron('cron_history',             
                                      format='rss')
            add_link(req, 'alternate', rss_href, _('RSS Feed'),
                     'application/rss+xml', 'rss')
            return 'cron_history.html', data
        
    def _displayListenerView(self, data={}):
        listener_list = []
        for listener in self.cron_listener_list:
            listener_data = {
                             'id': listener.getId(),
                             'enabled':self.cronconf.is_task_listener_enabled(listener) ,
                             'description': listener.getDescription()
                            }
            listener_list.append(listener_data)
        data["listener_list"] = listener_list
        
        return 'cron_listener.html', data
    
    def _saveSettings(self, req, category, page):
        arg_name_list = [self.cronconf.TICKER_ENABLED_KEY, self.cronconf.TICKER_INTERVAL_KEY]
        for task in self.cron_task_list:
            task_id = task.getId()
            arg_name_list.append(task_id + "." + self.cronconf.TASK_ENABLED_KEY)
            for schedule in self.all_schedule_type:
                schedule_id = schedule.getId()
                arg_name_list.append(task_id + "." + schedule_id)
                arg_name_list.append(task_id + "." + schedule_id + "." + self.cronconf.SCHEDULE_ENABLED_KEY)
                arg_name_list.append(task_id + "." + schedule_id + "." + self.cronconf.SCHEDULE_ARGUMENT_KEY)
        
        for arg_name in arg_name_list:
            arg_value = req.args.get(arg_name, "").strip()
            self.env.log.debug("receive req arg " + arg_name + "=[" + arg_value + "]")
            if (arg_value == ""):
                # dont't remove the key because of default value may be True
                if (arg_name.endswith(("." + self.cronconf.TASK_ENABLED_KEY, "." + self.cronconf.SCHEDULE_ENABLED_KEY))):
                    self.cronconf.set_value(arg_name, "False")
                else:
                    # otherwise we can remove the key
                    self.cronconf.remove_value(arg_name)
            else:
                self.cronconf.set_value(arg_name, arg_value)
        
        self._save_config(req)
        self.core.apply_config(wait=True)
        req.redirect(req.abs_href.admin(category, page))
        

    def _saveListenerSettings(self, req, category, page):
        arg_name_list = []
        for listener in self.cron_listener_list:
            listener_id = listener.getId()
            arg_name_list.append(listener_id + "." + self.cronconf.TASK_LISTENER_ENABLED_KEY)
        
        for arg_name in arg_name_list:
            arg_value = req.args.get(arg_name, "").strip()
            self.env.log.debug("receive req arg " + arg_name + "=[" + arg_value + "]")
            if (arg_value == ""):
                # dont't remove the key because of default value may be True
                if (arg_name.endswith("." + self.cronconf.TASK_ENABLED_KEY)):
                    self.cronconf.set_value(arg_name, "False")
                else:
                    # otherwise we can remove the key
                    self.cronconf.remove_value(arg_name)
            else:
                self.cronconf.set_value(arg_name, arg_value)
        
        self._save_config(req)
        self.core.apply_config(wait=True)
        req.redirect(req.abs_href.admin(category, page))
        
    def _clearHistory(self, req, category, page):
        self.core.clearHistory()
        req.redirect(req.abs_href.admin(category, page))

    def _runtask(self, req):
        taskId = req.args.get('task','')
        
        taskWithId = filter(lambda x: x.getId() == taskId, self.cron_task_list)
        
        if len(taskWithId) == 0:
            self.env.log.error("The task with id %s was not found" % taskId)
            add_warning(req, "The task with id %s was not found" % taskId)
            req.redirect(req.href.admin('traccron','cron_admin'))
        elif len(taskWithId) > 1:
            self.env.log.error("Multiple task with id %s was not found" % taskId)
            add_warning(req, "Multiple task with id %s was not found" % taskId) 
            req.redirect(req.href.admin('traccron','cron_admin'))
        else:
            task = taskWithId[0]
           
            #create parameters list if needed
            value = req.args.get('parameters', None)            
            if value:               
                parameters = [item.strip() for item in value.split(',')]
                self.core.runTask(task, parameters=parameters)
            else:           
                self.core.runTask(task)
            req.redirect(req.href.admin('traccron','cron_history'))
