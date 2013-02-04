# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''
###############################################################################
##
##        O U T    O F    T H E    B O X    T A S K    L I S T E N E R
##
###############################################################################

from time import  time, localtime

from trac.core import Component, implements, ExtensionPoint
from trac.notification import NotifyEmail
from trac.web.chrome import ITemplateProvider
from traccron.api import ITaskEventListener, IHistoryTaskExecutionStore
from traccron.core import CronConfig

class NotificationEmailTaskEvent(Component, ITaskEventListener, ITemplateProvider):
    """
    This task listener send notification mail about task event.
    """
    implements(ITaskEventListener)
    
    
    class NotifyEmailTaskEvent(NotifyEmail):
            
            template_name  = "notify_task_event_template.txt"
            
            def __init__(self, env):
                NotifyEmail.__init__(self, env)
                self.cronconf = CronConfig(self.env)

            def get_recipients(self, resid):
                """
                Return the recipients as defined in trac.ini.                
                """
                reclist = self.cronconf.get_email_notifier_task_recipient_list()     
                return (reclist, [])
                
            
            def notifyTaskEvent(self, task_event_list):
                """
                Send task event by mail if recipients is defined in trac.ini
                """
                self.env.log.debug("notifying task event...")             
                if self.cronconf.get_email_notifier_task_recipient() :                                    
                    # prepare the data for the email content generation
                    mess = ""      
                    start = True
                    for event in task_event_list:
                        if start:                        
                            mess = mess + "task[%s]" % (event.task.getId(),)                       
                            mess = mess + "\nstarted at %d h %d" % (event.time.tm_hour, event.time.tm_min)
                            mess = mess + "\n"
                        else:
                            mess = mess + "ended at %d h %d" % (event.time.tm_hour, event.time.tm_min)
                            if (event.success):
                                mess = mess + "\nsuccess"
                            else:
                                mess = mess + "\nFAILURE"
                            mess = mess + "\n\n"
                        start = not start                            

                    self.data.update({
                                     "notify_body": mess,                                        
                                      })                                          
                    NotifyEmail.notify(self, None, "task event notification")
                else:
                    self.env.log.debug("no recipient for task event, aborting")

            def send(self, torcpts, ccrcpts):
                return NotifyEmail.send(self, torcpts, ccrcpts)

    
    
    def __init__(self):        
        self.cronconf = CronConfig(self.env)
        self.task_event_buffer = []
        self.task_count = 0
        self.notifier = None
    
    
    class StartTaskEvent():
        """
        Store the event of a task start
        """
        def __init__(self, task):
            self.task = task
            self.time = localtime(time())
    
    
    class EndTaskEvent():
        """
        Store the event of a task end
        """
        def __init__(self, task, success):
            self.task = task
            self.time = localtime(time())
            self.success = success
            
            
            
    def get_htdocs_dirs(self):
        return []


    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    
    def onStartTask(self, task):
        """
        called by the core system when the task is triggered,
        just before the waek_up method is called
        """
        self.task_event_buffer.append(NotificationEmailTaskEvent.StartTaskEvent(task)) 
        self.task_count = self.task_count + 1

    def onEndTask(self, task, success):
        """
        called by the core system when the task execution is finished,
        just after the task wake_up method exit
        """
        if (self.cronconf.is_email_notifier_only_error() and success):
            self.task_event_buffer.pop()
            self.task_count -= 1
            return
        self.task_event_buffer.append(NotificationEmailTaskEvent.EndTaskEvent(task, success))
        # if the buffer reach the count then we notify
        if ( self.task_count >= self.cronconf.get_email_notifier_task_limit()):
            # send the mail
            if not self.notifier:
                self.notifier = NotificationEmailTaskEvent.NotifyEmailTaskEvent(self.env)
            self.notifier.notifyTaskEvent(self.task_event_buffer)
            
            # reset task event buffer
            self.task_event_buffer[:] = []
            self.task_count= 0

    def getId(self):
        return self.cronconf.EMAIL_NOTIFIER_TASK_BASEKEY
    
    def getDescription(self):
        return self.__doc__
    
class HistoryTaskEvent(Component,ITaskEventListener):
    """
    This task event listener catch task execution to fill all History store in its environment
    """
    
    implements(ITaskEventListener)
    
    history_store_list = ExtensionPoint(IHistoryTaskExecutionStore)
    
    
    def onStartTask(self, task):
        """
        called by the core system when the task is triggered,
        just before the wake_up method is called
        """
        self.task = task
        self.start = time()

    def onEndTask(self, task, success):
        """
        called by the core system when the task execution is finished,
        just after the task wake_up method exit
        """ 
        # currently Core assume that task are not threaded so any end event     
        # match the previous start event
        assert task.getId() == self.task.getId()
        self.end = time()
        self.success = success
        
        # notify all history store
        self._notify_history()
    
    def getId(self):
        """
        return the id of the listener. It is used in trac.ini
        """
        return "history_task_event"
    
    def getDescription(self):
        return self.__doc__
    
    def _notify_history(self):
        for historyStore in self.history_store_list:
            historyStore.addExecution(self.task, self.start, self.end, self.success)
            
