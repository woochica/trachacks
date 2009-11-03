import os
import fileinput
import re
from trac.core import *

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
     self.env.log.debug('Logfile name: %s' % (name,))
     return name

  def get_log(self, logname, req):
     """Retrieve the logfile content
     @param logname     : name of the logfile
     @param req
     @return array [0..n] of {level,line}
     """
     level = req.args.get('level')
     up = req.args.get('up')
     invert = req.args.get('invertsearch')
     regexp = req.args.get('regexp')
     tail = int(req.args.get('tail') or 0)
     tfilter = req.args.get('filter')
     levels  = ['', 'CRITICAL:', 'ERROR:', 'WARNING:', 'INFO:', 'DEBUG:']
     classes = ['', 'log_crit', 'log_err', 'log_warn', 'log_info', 'log_debug']
     log = []
     logline = {}
     level = int(level)
     try:
       f = open(logname,'r')
       lines = f.readlines()
       f.close
       linecount = len(lines)
       if tail: start = linecount - tail
       else: start = 0
       for i in range(start,linecount):
         line = lines[i]
         if tfilter:
           if regexp:
             if not invert and not re.search(tfilter,line): continue
             if invert and re.search(tfilter,line): continue
           else:
             if not invert and line.find(tfilter)==-1: continue
             if invert and not line.find(tfilter)==-1: continue
         logline = {}
         if line.find(levels[level])!=-1:
           logline['level'] = classes[level]
           logline['line']  = line
           log.append(logline)
         elif up:
           i = level
           found = False
           while i > 0:
             if line.find(levels[i])!=-1:
               logline['level'] = classes[i]
               logline['line']  = line
               log.append(logline)
               found = True
             i -= 1
           if not found and re.search('^[^0-9]+',line):
             logline['level'] = 'log_other'
             logline['line']  = line
             log.append(logline)
     except IOError:
       self.env.log.debug('Could not read from logfile!')
     return log
