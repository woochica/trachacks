# -*- coding: utf-8 -*-

from datetime import *
import re


class RenderImpl():
  '''
    Renderer implementation baseclass
  '''
  FRAME_LABEL = 'Project Plan'

  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
  
  def getTitle(self):
    if self.macroenv.macrokw.get('title') != None:# title of the visualization
      #self.macroenv.tracenv.log.debug('title=%s' % (self.macroenv.macrokw.get('title'),))
      return self.macroenv.macrokw.get('title')
    else:
      return None

  
  def getHeadline( self ):
    '''
      overwrite the method 
      TODO: make abstract
    '''
    title = self.getTitle()
    if title != None:
      return('%s' % (title,))
    else:
      return('%s' % (self.FRAME_LABEL,))
  
  def log_warn( self, message ):
    '''
      shortcut: warn logging
    '''
    self.macroenv.tracenv.log.warn(message)
  
  def getDateFormat( self ):
    return(self.macroenv.conf.get( 'ticketclosedf' ))
  
  def parseTimeSegment( self, timestr ):
    '''
      check for alias names in time strings, like TODAY+1
      currently only days are checked
    '''
    pat = re.compile(r'today\s*(\+|-)\s*(\d+)')
    if timestr.lower().startswith('today'): # today string
      today = date.today()
      
      matchs = pat.search(timestr)
      if matchs == None: # no calculation
        newtime = today
      else: # shift of time (by days)
        groups = matchs.groups()
        
        if groups[0] == '+':
          self.macroenv.tracenv.log.warn('parseTimeSegment ('+timestr+'): + '+repr(groups)+' '+groups[1])
          newtime = today + timedelta(days=int(groups[1]))
        else: # groups[0] == '-'
          self.macroenv.tracenv.log.warn('parseTimeSegment ('+timestr+'): - '+repr(groups)+' '+groups[1])
          newtime = today - timedelta(days=int(groups[1]))
      
      # export time to needed dateformat
      dateformat = self.getDateFormat();
      day = str(newtime.day).rjust(2, '0')
      month = str(newtime.month).rjust(2, '0')
      year = str(newtime.year).rjust(4, '0')
      if dateformat == 'MM/DD/YYYY':
        return ('%2s/%2s/%4s' % (month,day,year  ) )
      elif dateformat == 'DD/MM/YYYY':
        return ('%2s/%2s/%4s' % (day, month, year ) )
      elif dateformat == 'DD-MM-YYYY':
        return ('%2s-%2s-%4s' % (day, month, year ) )
      elif dateformat == 'YYYY-MM-DD':
        return ('%4s-%2s-%2s' % (day, month, year ) )
      else: # dateformat == 'YYYY-MM-DD':
        return ('%4s-%2s-%2s' % (day, month, year ) )
      
    else: # change nothing
      return timestr

  def getDateOfSegment( self, timestr ):
    try:
      dateformat = self.getDateFormat();
      if dateformat == 'MM/DD/YYYY':
        day = timestr[3:5]
        month = timestr[0:2]
        year = timestr[6:10]
      elif dateformat == 'DD/MM/YYYY':
        day = timestr[0:2]
        month = timestr[3:5]
        year = timestr[6:10]
      elif dateformat == 'DD-MM-YYYY':
        day = timestr[0:2]
        month = timestr[3:5]
        year = timestr[6:10]
      elif dateformat == 'YYYY-MM-DD':
        day = timestr[8:10]
        month = timestr[5:7]
        year = timestr[0:4]
      else: # dateformat == 'YYYY-MM-DD':
        day = timestr[8:10]
        month = timestr[5:7]
        year = timestr[0:4]
      self.macroenv.tracenv.log.debug('getDateOfSegment: year=%s,month=%s,day=%s' % (year,month,day))
      return(date(int(year),int(month),int(day)))
    except Exception,e:
      self.macroenv.tracenv.log.warn('getDateOfSegment: '+str(e)+' '+dateformat+' '+timestr)
      return None

  def render(self, ticketset):
    '''
      Generate Output and Return XML/HTML Code/Tags suited for Genshi
    '''
    pass
    
    
