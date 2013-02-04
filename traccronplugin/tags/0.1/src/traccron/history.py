# -*- encoding: UTF-8 -*-
'''
Created on 28 oct. 2010

@author: thierry
'''

###############################################################################
##
##        O U T    O F    T H E    B O X    H I S T O R Y    S T O R E
##
###############################################################################

from trac.core import Component, implements
from traccron.api import IHistoryTaskExecutionStore

class MemoryHistoryStore(Component, IHistoryTaskExecutionStore):
    
    implements(IHistoryTaskExecutionStore)
    
    history = []
    
    def addExecution(self, task, start, end, success):
        """
        Add a new execution of a task into this history
        """
        self.history.append((task,start,end,success))
    
    def getExecution(self, task=None, fromTime=None, toTime=None, sucess=None):
        """
        Return a iterator on all execution stored. Each element is a tuple
        of (task, start time, end time, success status)
        """
        for h in self.history:
            yield h
    