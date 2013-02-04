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

class CronScheduler(Component, SchedulerType):
    """
    Scheduler that used a cron-like syntax to specified when task must be triggered
    """
    def __init__(self):
        SchedulerType.__init__(self)

        # Some utility classes / functions first
    class AllMatch(set):
        """
        Universal set - match everything
        Stand for * in cron expression
        """
        def __contains__(self, item): return True

    class OmitMatch(AllMatch):
        """
        Stand for ? in cron expression
        """
        pass        
    
    class CronExpressionError(Exception):
        pass
    
    _allMatch = AllMatch()
    _omitMatch = OmitMatch()
    _event_parameter_for_cron_pos = {0:None, 1:"min",2:"hour",3:"day",4:"month",5:"dow",6:"year"}   

    # The actual Event class
    class Event(object):
        
        
        
        def __init__(self,  min, hour, 
                    day,  month, dow, year):
            self.mins = self.conv_to_set(min)
            self.hours= self.conv_to_set(hour)
            self.days = self.conv_to_set(day)            
            self.months = self.conv_to_set(month)
            self.dow = self.conv_to_set(dow)
            self.year = self.conv_to_set(year)

        def conv_to_set(self, obj):  # Allow single integer to be provided
            if isinstance(obj, (int,long)):
                return set([obj])  # Single item
            if not isinstance(obj, set):
                obj = set(obj)
                return obj
            else:
                return obj

        def matchtime(self, t):
            """Return True if this event should trigger at the specified localtime"""
            return ((t.tm_min     in self.mins) and
                    (t.tm_hour    in self.hours) and
                    (t.tm_mday    in self.days) and
                    (t.tm_mon     in self.months) and
                    (t.tm_wday    in self.dow) and
                    (t.tm_year    in self.year))



    def getId(self):
        return "cron"


    def getHint(self):
        return "use cron like expression"


    def compareTime(self, currentTime, schedule_value):
        
        if schedule_value:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with schedule_value " + schedule_value)
        else:
            self.env.log.debug(self.getId() + " compare currentTime=" + str(currentTime)  + " with NO schedule_value ")            
        if schedule_value:           
            try:
                kwargs = self._parse_cron_expression(cron=schedule_value)
            except CronScheduler.CronExpressionError:
                self.env.log.debug("Failed to parse cron expression, can't compare current time")
                return False
            else:
                return CronScheduler.Event(**kwargs).matchtime(t=currentTime)                
        else:
            return False   



    def _parse_cron_default(self, kwargs, event_param, value, min_value, max_value, adjust=0):
        """
        utility method to parse value of a cron item.
        Support of *, range expression (ex 1-10)
        adjust is used to translate value (ex: first day of week is 0 in python and 1 in Cron)
        """
        if value == "*":
            kwargs[event_param] = CronScheduler._allMatch
        else:
            begin, sep, end = value.partition("-")
            if sep == '-':
                # sanity check
                _begin = int(begin)
                _end = int(end)
                if (_begin < min_value):
                    self.env.log.error("invalid cron expression: start value of %s out of range [%d-%d] for %s" % (value,min_value,max_value, event_param))
                    raise CronScheduler.CronExpressionError() 
                if (_end > max_value):
                    self.env.log.error("invalid cron expression: end value of %s out of range [%d-%d] for %s" % (value,min_value,max_value,event_param))
                    raise CronScheduler.CronExpressionError()  
                # cron range expression is inclusive
                kwargs[event_param] = range(_begin + adjust, _end + 1 + adjust)
            else:
                begin, sep, step = value.partition("/")
                if  sep =='/':
                    # sanity check
                    _begin = int(begin)                
                    if ( ( _begin < min_value ) or ( _begin > max_value) ):
                        self.env.log.error("invalid cron expression: start value of %s out of range [%d-%d] for %s" % (value,min_value,max_value,event_param))
                        raise CronScheduler.CronExpressionError() 
                    _step = int(step)
                    # cron range expression is inclusive
                    kwargs[event_param] = range(_begin + adjust, max_value + 1 + adjust, _step)                                            
                else:
                    # assuming  int single value
                    _value = int(value)                
                    if (( _value < min_value ) or ( _value > max_value) ):                        
                        self.env.log.error("invalid cron expression: value of %s out of range [%d-%d] for %s" % (value, min_value, max_value, event_param))
                        raise CronScheduler.CronExpressionError() 

                    kwargs[event_param] = _value + adjust
    
        # range value

    def _parse_cron_dmonth(self, kwargs, __event_parameter_for_cron_pos, event_param, value):
        other_event_parm = __event_parameter_for_cron_pos.get(5)
        if value != '?':
            if kwargs.has_key(other_event_parm) and kwargs[other_event_parm] != '?':
                self.env.log.error("invalid cron expression: ? %s already have a value" % other_event_parm)
                raise CronScheduler.CronExpressionError()
        if value == '?':
            if kwargs.has_key(other_event_parm) and kwargs[other_event_parm] == '?':
                self.env.log.error("invalid cron expression: ? is already used for %s" % other_event_parm)
                raise CronScheduler.CronExpressionError()
            else:
                kwargs[event_param] = CronScheduler._omitMatch
        else:
            self._parse_cron_default(kwargs, event_param, value,1,31)       


    def _parse_cron_dweek(self, kwargs, __event_parameter_for_cron_pos, event_param, value):
        other_event_parm = __event_parameter_for_cron_pos.get(3)
        if value != '?':
            if kwargs.has_key(other_event_parm) and kwargs[other_event_parm] != '?':
                self.env.log.error("invalid cron expression: ? %s already have a value" % other_event_parm)
                raise CronScheduler.CronExpressionError()
        if value == '?':
            if kwargs.has_key(other_event_parm) and kwargs[other_event_parm] == '?':
                self.env.log.error("invalid cron expression: ? is already used for %s" % other_event_parm)
                raise CronScheduler.CronExpressionError()
            else:
                kwargs[event_param] = CronScheduler._omitMatch
        else:        
            # day of week starts at 1
            # since python localtime day of week start from 0
            self._parse_cron_default(kwargs, event_param, value, 1,7,adjust=-1)
    
               

    def _parse_cron_expression(self, cron):
        '''
        Parse cron expression and return dictionary of argument key/value suitable
        for Event object
        '''
        self.env.log.debug("parsing cron expression %s" % cron)
        kwargs = {}
        arglist = cron.split()
        if len(arglist) < 6:
            self.env.log.error("cron expression must have at least 6 items")
            raise CronScheduler.CronExpressionError()
        __event_parameter_for_cron_pos = CronScheduler._event_parameter_for_cron_pos
        for pos in __event_parameter_for_cron_pos.keys():                        
            event_param = __event_parameter_for_cron_pos.get(pos)                    
            if event_param and pos < len(arglist):                
                value = arglist[pos]                
                if pos == 1:
                    self._parse_cron_default(kwargs, event_param, value,0,59)
                elif pos == 2:
                    self._parse_cron_default(kwargs, event_param, value,0,23)
                elif pos == 3:
                    self._parse_cron_dmonth(kwargs, __event_parameter_for_cron_pos, event_param, value)
                elif pos == 4:
                    self._parse_cron_default(kwargs, event_param, value,1,12)
                elif pos == 5:
                    self._parse_cron_dweek(kwargs, __event_parameter_for_cron_pos, event_param, value)                   
                elif pos == 6:
                    self._parse_cron_default(kwargs, event_param, value,1970,2099)
                
        # deal with optional item
        year_parameter_name = __event_parameter_for_cron_pos.get(6)
        if not kwargs.has_key(year_parameter_name):
            kwargs[year_parameter_name] = CronScheduler._allMatch
        
        self.env.log.debug("result of parsing is %s" % str(kwargs))
        return kwargs