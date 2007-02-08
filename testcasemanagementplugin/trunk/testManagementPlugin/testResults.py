#!/usr/bin/env python

import re

import string
import os
import sys, traceback
import time
import logging
import logging.handlers
from trac.core import *

from testManager import ITestManagerRequestHandler

#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 
   

class TestResults(Component):
    implements(ITestManagerRequestHandler)
    
    def process_testmanager_request(self, req ):
                
        req.hdf['testcase.results.testcases']="gasArchive01"
        req.hdf['testcase.results.versions']="1.1.1"
        req.hdf['testcase.results.builds']="r1234"
        req.hdf['testcase.results.bugnumber']=""
        
        return 'testResults.cs', None
        

    def get_path( self, req ):
        return "results"
        
    def get_descriptive_name(self):
        return "Trac Test Results"

        


#env: The environment, an instance of the trac.env.Environment class (see trac.env). 
#config: The configuration, an instance of the trac.config.Configuration class (see trac.config). 
#log: The configured logger, see the Python logging API for more information. 



        

