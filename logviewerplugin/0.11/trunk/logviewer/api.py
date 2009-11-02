import os
import fileinput
from trac.core import *
from trac.config import *
from trac.env import Environment
from trac.perm import PermissionSystem, PermissionError

class LogViewerApi(Component):
  def get_logfile_name(self):
     """Get the name of the logfile used.
     Returns None if its not configured. Raises IOError if configured but not existing.
     @return logfile or None
     """
     if self.env.config.get('logging','log_type').lower()!='file': return None
     name = self.env.config.get('logging','log_file')
     fpath, fname = os.path.split(name)
     if not fpath: name = os.path.join(self.env.path,'log',name)
     if not os.path.exists(name): raise IOError
     self.env.log.info('Logfile name: %s' % (name,))
     return name

  def get_log(self, logname, level, up=True):
     """Retrieve the logfile content
     @param logname     : name of the logfile
     @param level       : log level to select
     @param optional up : whether to retrieve higher prios as well (default: True)
     @return array [0..n] of {level,line}
     """
     levels  = ['', 'CRITICAL:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']
     classes = ['', 'log_crit', 'log_err', 'log_warn', 'log_info', 'log_debug']
     log = []
     logline = {}
     level = int(level)
     #self.env.log.info('Processing log for level %i' % (level,))
     #if up: self.env.log.info('Higher prios also selected')
     try:
       #f = open(logname,'r')
       for line in fileinput.input(logname):
       #for line in f.readlines():
         logline = {}
         if line.find(levels[level])!=-1:
           logline['level'] = classes[level]
           logline['line']  = line
           log.append(logline)
         elif up:
           i = level
           while i > 0:
             if line.find(levels[i])!=-1:
               #self.env.log.info('Found entry for "%s"' % (levels[i],))
               logline['level'] = classes[i]
               logline['line']  = line
               log.append(logline)
             i -= 1
     except IOError:
       self.env.log.debug('Could not read from logfile!')
     self.env.log.info('%i lines shown' % (len(log),))
     fileinput.close()
     #f.close()
     return log
