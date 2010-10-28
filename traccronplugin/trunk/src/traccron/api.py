# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''

###############################################################################
##
##                     I N T E R F A C E    A P I
##
###############################################################################

from trac.core import Interface

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
        Return the key to use in trac.ini to configure this task
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
    
    

class ITaskEventListener(Interface):
    """
    Interface that listen to event occuring on task
    """    
    
    def onStartTask(self, task):
        """
        called by the core system when the task is triggered,
        just before the waek_up method is called
        """
        raise NotImplementedError

    def onEndTask(self, task, success):
        """
        called by the core system when the task execution is finished,
        just after the task wake_up method exit
        """
        raise NotImplementedError
    
    def getId(self):
        """
        return the id of the listener. It is used in trac.ini
        """
        raise NotImplementedError
    
class IHistoryTaskExecutionStore(Interface):
    """
    Interface that store an history of task execution. 
    """
    
    def addExecution(self, task, start, end, success):
        """
        Add a new execution of a task into this history.
        Task is the task object.
        start is the start time in second from EPOC
        end is the end time in seconf from EPOC
        """
        raise NotImplementedError
    
    def getExecution(self, task=None, fromTime=None, toTime=None, sucess=None):
        """
        Return a iterator on all execution stored. Each element is a tuple
        of (task, start time, end time, success status) where
        task is the task object
        start time and end time are second from EPOC
        success status is a boolean value 
        
        Optional paramater can be used to filter the result.
        """
        raise NotImplementedError
    
