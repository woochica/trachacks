# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''
###############################################################################
##
##          O U T    O F    T H E    B O X    S C H E D U L E R
##
###############################################################################

from trac.core import Component, implements    
from traccron.api import ISchedulerType
from traccron.core import CronConfig

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

