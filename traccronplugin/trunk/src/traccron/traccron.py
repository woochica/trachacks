# -*- encoding: UTF-8 -*-

'''
Created on 12 oct. 2010

@author: thierry
'''
from trac.core import *
from trac.notification import NotifyEmail, Notify
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import add_notice, add_warning
from trac.util.translation import _
from trac.util.text import exception_to_unicode
from threading import Timer
from time import  time, localtime

###############################################################################
##
##                     I N T E R F A C E    A P I
##
###############################################################################

class ICronTask(Interface):
    """
    Interface for component task
    """
    
    def wake_up(self, *args):
        """
        Call by the scheduler when the task need to be executed
        """
        raise NotImplementedError
    
    def getId(self):
        """
        Return the key to use in trac.ini to cinfigure this task
        """
        raise NotImplementedError
    
    def getDescription(self):
        """
        Return the description of this task to be used in the admin panel.
        """
        raise NotImplementedError
    

class ISchedulerType(Interface):
    """
    Interface for scheduler type. A Scheduler type is a sort of scheduler that
    can trigger a task based on a specific scheduling.
    """        

        
    def getId(self):
        """
        Return the id to use in trac.ini for this schedule type
        """
        raise NotImplementedError
    
    def getHint(self):
        """
        Return a description of what it is and the format used to defined the schedule
        """
        raise NotImplementedError
    
    def isTriggerTime(self, task, currentTime):
        """
        Test is accordingly to this scheduler and given currentTime, is time to fire the task
        """
        raise NotImplementedError
    

###############################################################################
##
##        C O R E    C L A S S E  S     O F     T H E    P L U G I N 
##
###############################################################################

class Core(Component):    
    """
    Main class of the Trac Cron Plugin. This is the entry point
    for Trac plugin architecture
    """    
    
    implements(IAdminPanelProvider, ITemplateProvider)
    
    cron_tack_list = ExtensionPoint(ICronTask)
    
    supported_schedule_type = ExtensionPoint(ISchedulerType)
    

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
                    if self.cronconf.is_schedule_enabled(task, schedule):
                        # run task if needed
                        if schedule.isTriggerTime(task, currentTime):
                            self.env.log.info("executing task " + task.getId());
                            try:
                                args = self.cronconf.get_schedule_arg_list(task, schedule)
                                task.wake_up(*args)
                            except Exception, e:
                                self.env.log.error('task execution result : FAILURE %s', exception_to_unicode(e))        
                            else:
                                self.env.log.info("task execution result : SUCCESS")
                                self.env.log.info("task " + task.getId() + " finished");
                        else:
                            self.env.log.debug("nothing to do for " + task.getId());
                    else:
                        self.env.log.debug("schedule " + schedule.getId() + " is disabled")
            else:
                self.env.log.debug("task " + task.getId() + " is disabled")

        
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
        
    def create_new_timer(self, wait=False):
        """
        Create a new timer before killing existing one if required.
        wait : if True the current thread wait until running task finished. Default is False
        """
        self.env.log.debug("create new ticker")
        if (self.timer != None):
            self.timer.cancel()
            if ( wait ):
                self.timer.join()            
        
        self.timer = Timer(self.interval * 60 , self.wake_up)
        self.timer.start()
        self.env.log.debug("new ticker started")

    def wake_up(self):
        self.env.log.debug("ticker wake up")
        self.callback()
        self.create_new_timer()
        
    
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
    
    def set_value(self, key, value):
        self.env.config.set(self.TRACCRON_SECTION, key, value)
    
    def remove_value(self, key):
        self.env.config.remove(self.TRACCRON_SECTION, key)
    
    def save(self):
        self.env.config.save()

class WebUi(IAdminPanelProvider, ITemplateProvider):
    """
    Class that deal with Web stuff. It is the both the controller and the page builder.
    """
    def __init__(self, core):        
        self.env = core.env
        self.cron_task_list = core.getTaskList()
        self.cronconf = core.getCronConf()
        self.all_schedule_type = core.getSupportedScheduleType()
        self.core = core
    
    def get_admin_panels(self, req):
        if ('TRAC_ADMIN' in req.perm) :
            yield ('tracini', 'trac.ini', 'cron_admin', u'Trac Cron')


    def render_admin_panel(self, req, category, page, path_info):
        req.perm.assert_permission('TRAC_ADMIN')
        
        data = {}
        
        if req.method == 'POST':
            if 'save' in req.args:          
                
                arg_name_list = [self.cronconf.TICKER_ENABLED_KEY,self.cronconf.TICKER_INTERVAL_KEY]
                for task in self.cron_task_list:                        
                    task_id = task.getId()                                       
                    arg_name_list.append(task_id + "." + self.cronconf.TASK_ENABLED_KEY)     
                    for schedule in self.all_schedule_type:
                        schedule_id = schedule.getId()
                        arg_name_list.append(task_id + "." + schedule_id)   
                        arg_name_list.append(task_id + "." + schedule_id + "." + self.cronconf.SCHEDULE_ENABLED_KEY)     
                        arg_name_list.append(task_id + "." + schedule_id + "." + self.cronconf.SCHEDULE_ARGUMENT_KEY)
                
                for arg_name in arg_name_list:                   
                    arg_value = req.args.get(arg_name,"").strip()
                    self.env.log.debug("receive req arg "+ arg_name + "=[" + arg_value + "]")
                    if (arg_value == ""):
                        # dont't remove the key because of default value may be True
                        if ( arg_name.endswith(("." + self.cronconf.TASK_ENABLED_KEY, "." + self.cronconf.SCHEDULE_ENABLED_KEY))):
                            self.cronconf.set_value(arg_name, "False")
                        # otherwise we can remove the key 
                        else:                                                  
                            self.cronconf.remove_value(arg_name)                        
                    else:
                        self.cronconf.set_value(arg_name, arg_value)                  
                
                self._save_config(req)
                self.core.apply_config(wait=True)
                req.redirect(req.abs_href.admin(category, page))
        else:            
            
            data.update({
                          self.cronconf.TICKER_ENABLED_KEY:self.cronconf.get_ticker_enabled(),
                          self.cronconf.TICKER_INTERVAL_KEY: self.cronconf.get_ticker_interval()                         
                          })
            
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
                                                                "enabled": task_enabled,
                                                                "arg" : task_arg
                                                            }
                task_data['schedule_list'] = all_schedule_value                        
                                        
                task_list.append(task_data)
            
            data['task_list'] = task_list
            return 'cron_admin.html', data
                

    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # internal method    


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



###############################################################################
##
##          O U T    O F    T H E    B O X    S C H E D U L E R
##
###############################################################################
    

class SchedulerType(ISchedulerType):
    """
    Define a sort of scheduling. Base class for any scheduler type implementation
    """
    
    implements(ISchedulerType)   
    
    def __init__(self):    
        self.cronconf = CronConfig(self.env)
                

        
    def getId(self):
        """
        Return the id to use in trac.ini for this schedule type
        """
        raise NotImplementedError
    
    def getHint(self):
        """
        Return a description of what it is and the format used to defined the schedule
        """
        return ""
    
    def isTriggerTime(self, task, currentTime):
        """
        Test is accordingly to this scheduler and given currentTime, is time to fire the task
        """
        # read the configuration value for the task
        self.env.log.debug("looking for schedule of type " + self.getId())
        for schedule_value in self._get_task_schedule_value_list(task):
            self.env.log.debug("task [" + task.getId() + "] is scheduled for " + schedule_value)
            if self.compareTime(currentTime, schedule_value):
                return True
        self.env.log.debug("no matching schedule found")
        return False
    
    def compareTime(self, currentTime, schedule_value):
        """
        Test is accordingly to this scheduler, given currentTime and schedule value,
        is time to fire the task.
        currentTime is a structure computed by time.localtime(time())
        scheduled_value is the value of the configuration in trac.ini      
        """
        raise NotImplementedError
    
    def _get_task_schedule_value_list(self, task):
        return self.cronconf.get_schedule_value_list(task, self)
    



class DailyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once a day based uppon a defined time
    """
    
    def __init__(self):
        SchedulerType.__init__(self)
        
    def getId(self):
        return "daily"
    
    def getHint(self):
        return "ex: 8h30 fire every day at 8h30" 
               
    
    def compareTime(self, currentTime, schedule_value):        
        # compare value with current
        if schedule_value:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with schedule_value " + schedule_value)
        else:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with NO schedule_value ")
        if schedule_value:
            return schedule_value == str(currentTime.tm_hour) + "h" + str(currentTime.tm_min)
        else:
            return False
         

class HourlyScheduler(Component,SchedulerType):
    """
    Scheduler that trigger a task once an hour at a defined time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    
    def getId(self):
        return "hourly"
    
    def getHint(self):
        return "ex: 45 fire every hour at 0h45 then 1h45 and so on" 
    
    def compareTime(self, currentTime, schedule_value):        
        # compare value with current
        if schedule_value:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with schedule_value " + schedule_value)
        else:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with NO schedule_value ")
        if schedule_value:
            return schedule_value == str(currentTime.tm_min)
        else:
            return False    


class WeeklyScheduler(Component,SchedulerType):
    """
    Scheduler that trigger a task once a week at a defined day and time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    
    def getId(self):
        return "weekly"
    
    def getHint(self):
        return "ex: 0@12h00 fire every monday at 12h00" 

    
    def compareTime(self, currentTime, schedule_value):        
        # compare value with current
        if schedule_value:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with schedule_value " + schedule_value)
        else:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with NO schedule_value ")
        if schedule_value:
            return schedule_value == str(currentTime.tm_wday) + "@" + str(currentTime.tm_hour) + "h" + str(currentTime.tm_min)
        else:
            return False    


class MonthlyScheduler(Component, SchedulerType):
    """
    Scheduler that trigger a task once a week at a defined day and time
    """

    def __init__(self):
        SchedulerType.__init__(self)

    
    def getId(self):
        return "monthly"
    
    def getHint(self):
        return "ex: 15@12h00 fire every month on the 15th day of month at 12h00" 

    
    def compareTime(self, currentTime, schedule_value):        
        # compare value with current
        if schedule_value:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with schedule_value " + schedule_value)
        else:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with NO schedule_value ")
        if schedule_value:
            return schedule_value == str(currentTime.tm_mday) + "@" + str(currentTime.tm_hour) + "h" + str(currentTime.tm_min)
        else:
            return False   




###############################################################################
##
##             O U T    O F    T H E    B O X    T A S K
##
###############################################################################


class HeartBeatTask(Component,ICronTask):
    """
    This is a simple task for testing purpose.
    It only write a trace in log a debug level
    """
    
    implements(ICronTask)
    
    def wake_up(self, *args):
        if len(args) > 0:
            for arg in args:
                self.env.log.debug("Heart beat: " + arg)
        else:
            self.env.log.debug("Heart beat: boom boom !!!")
    
    def getId(self):
        return "heart_beat"
    
    def getDescription(self):
        return self.__doc__
        

class SleepingTicketReminderTask(Component, ICronTask, ITemplateProvider):
    """
    Remind user about sleeping ticket they are assigned to.
    """
       
    implements(ICronTask, ITemplateProvider)
    
    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    
    def wake_up(self, *args):
        delay = 3        
        if len(args) > 0:
            delay = int(args[0])
        
        
        class SleepingTicketNotification(NotifyEmail):
            
            template_name  = "sleeping_ticket_template.txt"
            
            def __init__(self, env):
                NotifyEmail.__init__(self, env)

            def get_recipients(self, owner):
                return ([owner],[])

                
            
            def remind(self, tiketsByOwner):
                """
                Send a digest mail to ticket owner to remind him of those
                sleeping tickets
                """
                for owner in tiketsByOwner.keys():  
                    # prepare the data for the email content generation                      
                    self.data.update({
                                      "ticket_count": len(tiketsByOwner[owner]),
                                      "delay": delay
                                      })                                          
                    NotifyEmail.notify(self, owner, "Sleeping ticket notification")

            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)

            
        class OrphanedTicketNotification(NotifyEmail):
            
            template_name  = "orphaned_ticket_template.txt"
            
            def __init__(self, env):
                NotifyEmail.__init__(self, env)
                
            def get_recipients(self, reporter):
                 return ([reporter],[])
            
            def remind(self, tiketsByReporter):
                """
                Send a digest mail to the reporter to remind them
                of those orphaned tickets
                """
                for reporter in tiketsByReporter.keys():  
                    # prepare the data for the email content generation                      
                    self.data.update({
                                      "ticket_count": len(tiketsByReporter[owner]),
                                      "delay": delay
                                      })                                          
                    NotifyEmail.notify(self, reporter, "orphaned ticket notification")


            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)            
            
                                
        # look for ticket assigned but not touched since more that the delay       
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # assigned ticket
        cursor.execute("""
                SELECT t.id , t.owner  FROM ticket t, ticket_change tc                        
                WHERE  t.id = tc.ticket  
                AND    t.status in ('new','assigned','accepted')
                AND    (SELECT MAX(tc2.time) FROM ticket_change tc2 WHERE tc2.ticket=tc.ticket)  < %s GROUP BY t.id
            """, (time() - delay * 24 * 60 * 60,) )
        dico = {}
        for ticket, owner in cursor:
            self.env.log.info("warning ticket %d assigned to %s but is inactive since more than %d day" % (ticket, owner, delay))
            if dico.has_key(owner):
                dico[owner].append(ticket)
            else:
                dico[owner] = [ticket]
        SleepingTicketNotification(self.env).remind(dico)
        # orphaned ticket
        cursor.execute("""
               SELECT t.id, t.reporter  FROM  ticket t
               WHERE  t.id not in (select tc.ticket FROM ticket_change tc WHERE tc.ticket=t.id)
               AND t.time < %s AND t.status = 'new'
            """, (time() - delay * 24 * 60 * 60,) )
        dico = {}
        for ticket, reporter in cursor:
            self.env.log.info("warning ticket %d is new but orphaned" % (ticket,))
            if dico.has_key(reporter):
                dico[reporter].append(ticket)
            else:
                dico[reporter] = [ticket]
        OrphanedTicketNotification(self.env).remind(dico)
    
    def getId(self):
        return "sleeping_ticket"
    
    def getDescription(self):
        return self.__doc__
    

    
