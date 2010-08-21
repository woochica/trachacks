# -*- coding: utf-8 -*-

'''
  ALPHA
  TODO: starttime, endtime
'''


import string
import datetime
import time
from genshi.builder import tag
from genshi.input import HTMLParser
from genshi.core import Stream as EventStream, Markup
from genshi.template.markup import MarkupTemplate

from pprenderimpl import RenderImpl
from trac.web.chrome import add_stylesheet, add_script

class ChartRenderer(RenderImpl):
  '''
    render a chart of values
    a javascript renderer is used
  '''
  fielddefault = 'status'
  weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su' ]
  
  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def getHeadline( self ):
    return('Burn-down Chart')

 
  def getField( self ):
    '''
      returns the user configuration or default which field should be observed
    '''
    return self.macroenv.macrokw.get( 'field', self.fielddefault )

  def getNameOfRenderFrame(self): 
    return( '__insert_key_here__'+str(self.macroenv.macrokw.get( 'macroid', 'defaultid')) )

  def datetime2seconds( self, dt ):
    return time.mktime(dt.timetuple())

  def seconds2datetime( self, secs ):
    return(datetime.datetime.fromtimestamp(secs))

  def getDayString( self, mytime ) :
    '''
      input seconds, returns year month day space-separated
    '''
    #return datetime.datetime.fromtimestamp(mytime).strftime("%Y-%m-%d %H:%M")
    if isinstance(mytime, float):
      return datetime.datetime.fromtimestamp(mytime).strftime("%Y-%m-%d")
    elif isinstance(mytime, datetime.date) or isinstance(mytime, datetime.datetime) :
      return mytime.strftime("%Y-%m-%d")
    else:
      raise Exception('Unknown date: %s' % (mytime,))

  def setKeyIfNotExists( self, mylist, newkey ):
    '''
      call-by-reference
    '''
    if not mylist.has_key(newkey) :
      mylist[newkey] = []

  def getFirstKey( self, keys ):
    '''
      returns the first date
      precondition: keys is not empty
    '''
    return keys[0]

  def getFirstSegment( self, keys ):
    return self.getSegmentLimit( self.firstsegment, keys[0], True )

  def getLastSegment( self, keys ):
    key = self.getSegmentLimit( self.lastsegment, keys[ len(keys) - 1], False  )
    currentday = self.datetime2seconds( datetime.date.today() )
    if key < currentday:
      return currentday
    else:
      return key
 
  def getSegmentLimit( self, macroparam, availablevalue, searchfirst ):
    '''
      TODO: extend
    '''
    
    if macroparam == '': # no parameter setted
      return self.datetime2seconds(self.string2date(availablevalue))
    elif macroparam.lower().strip() in weekdays: # dynamic week day setted
      weekdaysearched = macroparam.lower().strip()
      # self.macroenv.tracenv.log.debug(str(searchfirst)+' param: '+'('+str(weekdaysearched)+')' )
      if searchfirst:
        daydiff = datetime.timedelta(days=-1)
        offset = datetime.timedelta(days=0)
      else:
        daydiff = datetime.timedelta(days=1)
        offset = datetime.timedelta(days=-1) # hack: offset to move last day 
      
      # search for the next/last day which is such a week day
      weekdaykey = 0
      for i in range(len(weekdays)): # search for the key TODO: improve
        if weekdays[i] == weekdaysearched:
          weekdaykey = i
      #self.macroenv.tracenv.log.debug('weekdaykey: '+str(weekdaykey)+' '+str(weekdaysearched) )
      
      currentday = datetime.date.today()
      while currentday.weekday() != weekdaykey :
        #self.macroenv.tracenv.log.warning('search: '+str(currentday)+' '+str(currentday.weekday())+' ('+str(weekdaysearched)+'  '+str(weekdaykey)+')' )
        currentday = currentday + daydiff
      
      currentday = currentday + offset
      self.macroenv.tracenv.log.debug(str(searchfirst)+' found: '+str(currentday)+' ('+str(weekdaysearched)+')' )
      
      return self.datetime2seconds(currentday) # the day sufficies the user parameter
      
    else:
      return self.datetime2seconds(self.string2date(macroparam))
  
  
  
  
  def normalizeToDay(self, sec):
    '''
      translate day-seconds to seconds equilvalent to YYYY-MM-DD 00:00:01
    '''
    self.macroenv.tracenv.log.debug("normalizeToDay pre : "+str(sec))
    #self.macroenv.tracenv.log.warning("normalizeToDay pre : "+datetime.datetime.fromtimestamp(sec).strftime("%Y-%m-%d %H:%M:%S")+"  "+str(sec % 86400)  )
    #r = ( ( sec - (sec % 86400) ) + 1 )
    
    dt = datetime.datetime.fromtimestamp(sec)
    return( self.datetime2seconds(datetime.datetime( int(dt.year), int(dt.month), int(dt.day), 0, 0, 1)) )
  
  def fillUpByDates( self, datedict ):
    '''
      date is the key
      call-by-reference
    '''
    keys = datedict.keys()
    keys.sort()
    daydiff = datetime.timedelta(days=1)
    (firstday, lastday) = self.getBoundaries( datedict )
    
    newdatedict = {}
    
    # get datetime from float time
    if firstday < keys[0] :
      firstfloat = self.normalizeToDay(firstday) 
    else:
      firstfloat = self.normalizeToDay(keys[0])  # if earlier values need to be propagated
    currentday = datetime.datetime.fromtimestamp(firstfloat)
    lastday = datetime.datetime.fromtimestamp(lastday) 
    
    # add changes to each day
    for key in keys:
      normalizedkey = self.normalizeToDay(key)
      self.macroenv.tracenv.log.debug('normalizedkey='+repr(self.getDayString(normalizedkey))+' '+repr(normalizedkey) )
      if not newdatedict.has_key( normalizedkey ):
        newdatedict[normalizedkey] = []
      newdatedict[normalizedkey] = newdatedict[normalizedkey] + datedict[key]
    self.macroenv.tracenv.log.debug('newdatedict='+repr(newdatedict))
    
    
    
    # remove duplicate entries, save per day
    # get last value of each ticket
    # precondition: entries are sorted by date
    aggredateddict = {}
    for key in newdatedict.keys():
      
      lastticketvalues = {}
      for (ticketid,val) in newdatedict[key] :
        #self.macroenv.tracenv.log.warning('lastticketvalues set:'+str(ticketid)+'='+str(val)) 
        lastticketvalues[ticketid] = val
      
      # add all ticket values
      valuesum = 0.0
      for ticketid in lastticketvalues.keys():
        self.macroenv.tracenv.log.debug('lastticketvalues:'+str(ticketid)+'='+str(lastticketvalues[ticketid])) 
        valuesum += lastticketvalues[ticketid]
      
      aggredateddict[key] = valuesum
    
    # initialize each missing day
    oldvalue = 0.0
    while currentday <= lastday : # including the last day
      #self.macroenv.tracenv.log.warning('aggredateddict: currentday='+repr(currentday)+'   '+str(self.datetime2seconds(currentday)))
      if not aggredateddict.has_key(self.datetime2seconds(currentday)):
        aggredateddict[self.datetime2seconds(currentday)] = oldvalue
      else:
        oldvalue = aggredateddict[self.datetime2seconds(currentday)]
      currentday = currentday + daydiff
    
    #self.macroenv.tracenv.log.warning('aggredateddict='+repr(aggredateddict) )
    
    return aggredateddict

  def string2date( self, mystring ):
    '''
      a string YYYY-MM-DD is translated into the corresponding datetime
      float timestamp can be handled to
    '''
    if isinstance(mystring, float): # fallback if float
      mystring = self.getDayString(mystring)
    
    tmp = string.split( mystring, "-")
    return datetime.datetime( int(tmp[0]), int(tmp[1]), int(tmp[2]) )

  def addJsChartFiles( self ):
    '''
      add css and javascript files
    '''
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/raphael.js' )
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/raphael_002.js' )
    add_script( self.macroenv.tracreq, 'projectplan/js/jquery-burndown/burndown.js' )

  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    return tag.div('base class chart renderer: no rendering')

#RenderRegister.add( SimpleRenderer, 'simplerender' )




class BurndownChart(ChartRenderer):
  '''
    check tickets not closed at the given 
  '''
  segment = ''
  segmentDefault = 'day'
  firstsegment = ''
  lastsegment = ''
  
  def __init__(self, macroenv ):
    ChartRenderer.__init__(self, macroenv)
    # width of chart
    self.width = int(self.macroenv.macrokw.get( 'width', '800').strip())
    # height of chart
    self.height = int(self.macroenv.macrokw.get( 'height', '250').strip())
    # time segment of x-axis: days or week
    self.segment = self.macroenv.macrokw.get( 'segment', '').strip()
    if not ( self.segment in ['day', 'week', 'month', 'year'] ) :
      #self.segment = self.segmentDefault # default time segment style
      raise Exception('Unknown segment configuration: '+str(self.segment))
    
    self.firstsegment = self.macroenv.macrokw.get( 'first', '').strip()
    self.lastsegment = self.macroenv.macrokw.get( 'last', '').strip()
    if self.firstsegment == '':
      self.firstsegment = None
    if self.lastsegment == '':
      self.lastsegment = None

  def getEndOfSegment( self, changeday ):
    if self.segment == 'day':
      return(changeday)
    elif self.segment == 'week':
      dt = self.seconds2datetime(changeday)
      end = dt + datetime.timedelta( days = (7 - dt.isoweekday() - 1) ) # end of week: saturday
      #end = dt + datetime.timedelta( days = (7 - dt.weekday()) ) # end of week: sunday
      return(self.datetime2seconds(end))
    elif self.segment == 'month':
      dt = self.seconds2datetime(changeday)
      end = dt + datetime.timedelta( days = 31 ) # next month
      return(self.datetime2seconds( datetime.datetime( end.year, end.month, 1 ) - datetime.timedelta( days = 1) )) # last day of month
    elif self.segment == 'year':
      dt = self.seconds2datetime(changeday)
      end = self.datetime2seconds(  datetime.datetime( dt.year, 12, 31, 23, 59, 59 ) )
      return end
    else:
      raise Exception('Unknown segment configuration: '+str(self.segment))

  def getSegmentString( self, changeday ):
    if self.segment == 'day':
      return self.getDayString(changeday)
    if self.segment == 'week':
      dt = self.seconds2datetime(changeday)
      return 'week '+str(dt.isocalendar()[1])+'/'+str(dt.isocalendar()[0])
    if self.segment == 'month':
      dt = self.seconds2datetime(changeday)
      return str(dt.month)+' / '+str(dt.year)
    if self.segment == 'year':
      dt = self.seconds2datetime(changeday)
      return str(dt.year)

  def aggregateDates( self, changes ):
    '''
      dict (key: time) is aggregated
    '''
    newchanges = {}
    if self.segment == 'day' : # no change, as days already
      return changes
    else: # week, month
      newchanges = {}
      keys = changes.keys()
      keys.sort()
      for changeday in keys:
        endofsegment = self.getEndOfSegment(changeday)
        self.setKeyIfNotExists( newchanges, endofsegment )
        self.macroenv.tracenv.log.debug("aggregateDates: "+self.segment+": "+self.getDayString(endofsegment)+" = "+str(changes[changeday])+"  "+self.getDayString(changeday) )
        newchanges[endofsegment] = changes[changeday]
      return newchanges

  def getBoundariesConf( self ):
    '''
      returns the macro parameters
    '''
    first = self.firstsegment
    last = self.lastsegment
    
    daydiff = datetime.timedelta(days=1)
    
    if first != None: 
      if first.lower() in self.weekdays:
        first = first.lower()
        currentday = datetime.datetime.today()
        self.macroenv.tracenv.log.debug("first weekday: "+str(currentday.weekday() ))
        while self.weekdays[currentday.weekday()].lower() != first:
          currentday = currentday - daydiff
        first = self.datetime2seconds(currentday)
        self.macroenv.tracenv.log.debug("first weekday: "+self.getDayString(first)+' param:'+str(first) )
      else:
        first = self.datetime2seconds(self.string2date( first ))
    
    if last != None:
      if last.lower() in self.weekdays:
        last = last.lower()
        currentday = datetime.datetime.today()
        self.macroenv.tracenv.log.debug("last weekday: "+str(currentday.weekday() ))
        
        if first == last : # add one day, if e.g. "fr" to "fr"
          current = current + daydiff
        
        while self.weekdays[currentday.weekday()].lower() != last:
          currentday = currentday + daydiff
        last = self.datetime2seconds(currentday)
        self.macroenv.tracenv.log.debug("last weekday: "+self.getDayString(last)+' param:'+str(last) )
      else:
        last = self.datetime2seconds(self.string2date( last )) 
    
    return ( first, last )
  
  def getBoundaries( self, datedict ):
    '''
      returns a tuple (firstday,lastday)
    '''
    keys = datedict.keys()
    keys.sort()
    
    nowInSeconds = self.datetime2seconds( datetime.datetime.today() )
    
    # save values in keys
    if len(keys) > 0 :
      firstdayInKeys = keys[0]
      lastdayInKeys = keys[ len(keys) - 1] 
    else:
      firstdayInKeys = self.datetime2seconds( datetime.date.today() )
      lastdayInKeys = firstdayInKeys
    
    (firstdayConf, lastdayConf) = self.getBoundariesConf()
    
    # use the marco parameter if set
    if firstdayConf != None:
      firstday = firstdayConf
    else:
      firstday = firstdayInKeys
    
    if lastdayConf != None:
      lastday = lastdayConf
    else:
      if lastdayInKeys < nowInSeconds:
        lastday = nowInSeconds
      else:
        lastday = lastdayInKeys
    
    firstday = self.normalizeToDay(firstday) # seconds of YYYY-MM-DD  HH:ii:01
    lastday = self.normalizeToDay(lastday) # seconds of YYYY-MM-DD  HH:ii:01
    
    self.macroenv.tracenv.log.debug("getBoundaries: firstday=%s (%s) lastday=%s (%s)" % (firstday,self.getDayString(firstday), lastday,self.getDayString(lastday) ) )
    
    return (firstday, lastday)

  def getLabel( self ):
    '''
      labels of chart
    '''
    field = self.getField() 
    if field == 'status':
      return(('tickets left: ', 'tickets closed: '))
    else:
      return((''+field+': ', 'reduced by: '))
  
  def getValue( self, field, value ):
    '''
      translate value to float 
    '''
    #self.macroenv.tracenv.log.warning('field: '+str(value))
    if field == 'status': # special evaluation at status values
      if value in ['closed']:
        return -1.0 # one active ticket less
      elif value in ['reopened', 'new']:
        return 1.0 # one active ticket more
      else:
        return 0.0 # not interesting
    else:
      try:
        return float(value)
      except:
        return 0.0 # fallback

  def render(self, ticketset):
    # add needed javascript and css files
    self.addJsChartFiles()
    
    
    frame = tag.div( class_= 'invisible ppConfBurnDown', id=self.getNameOfRenderFrame() )
    tickets = ticketset.getIDList()
    
    # stop if no tickets available
    if len(tickets) == 0:
      return tag.div('No tickets available.')
    
    changes = {}    
    fieldconf = self.getField()
    initalvalues = {}
    creationdates = {}
    
    # initialize, so it is usable below
    for tid in tickets :
      ticket = ticketset.getTicket(tid)
      changetime = ticket.getfield('time') # creation date
      changetimestr = self.datetime2seconds(changetime) 
      creationday = self.getDayString(changetime)
      creationdates[tid] = changetimestr
      self.setKeyIfNotExists( changes, changetimestr) 
      
      # save the changes of each ticket to an array
      changelog = ticketset.get_changelog(tid)
      changelog.reverse() # initial value at last
      for changetime, author, field, oldvalue, newvalue, perm in changelog:
        if field == fieldconf:
          changetimestr = self.datetime2seconds(changetime) 
          self.setKeyIfNotExists( changes, changetimestr)
          val = self.getValue( fieldconf, newvalue )
          #self.macroenv.tracenv.log.warning("newvalue: "+str(tid)+"="+str(val))
          changes[changetimestr].append((tid,val))
          # save initial values
          val = self.getValue( fieldconf, oldvalue )
          #self.macroenv.tracenv.log.warning("oldvalue: "+str(tid)+"="+str(val))
          changes[creationdates[tid]].append(( tid, val ))
          self.macroenv.tracenv.log.debug("ticket_changes: %4s %s %5s --> %5s  %s %s" % ("#"+str(tid),field,oldvalue,newvalue,changetime, author)  )
          #inner = tag.tr() # DEBUG
          #inner(tag.td(tid)) # DEBUG
          #inner(tag.td(field)) # DEBUG
          #inner(tag.td(oldvalue)) # DEBUG
          #inner(tag.td('-->')) # DEBUG
          #inner(tag.td(newvalue)) # DEBUG
          #inner(tag.td(changetime)) # DEBUG
          #inner(tag.td(author)) # DEBUG
          #outer(inner) # DEBUG
    
    maxTicketnumberComplete = -1 # init
    changes = self.fillUpByDates(changes) 
    changes = self.aggregateDates(changes)
    #self.macroenv.tracenv.log.debug('changes='+repr(changes)) # DEBUG
    
    outer2 = tag.table( class_="invisibleX data" , border = "1", style = 'width:auto;')
    keys = changes.keys()
    keys.sort() # sort by time
    self.macroenv.tracenv.log.debug('aggregated keys='+repr(keys)) # DEBUG
    self.macroenv.tracenv.log.debug('changes='+repr(changes)) # DEBUG
    
    (firstday, lastday) = self.getBoundaries( changes )
    firstsegment = firstday
    lastsegment = lastday
    
    trDays = tag.tr()
    trDaysAxis = tag.tr()
    trOpenTickets = tag.tr()
    trClosedTickets = tag.tr()
    trReopenedTickets = tag.tr()
    valuesum = 0.0
    previoussum = 0.0
    today = self.normalizeToDay( self.datetime2seconds( datetime.datetime.today() ) )
    todayid = 0
    # compute the table holding the relevant values
    firstday = self.normalizeToDay(firstday)
    lastday = self.normalizeToDay(lastday)
    
    for changetime in keys :
      
      dayvalue = 0.0
      closed = 0.0
      reopened = 0.0
      
      #valuesum = 0.0
      self.macroenv.tracenv.log.debug('- changes['+str(changetime)+'] '+self.getDayString(changetime)+'='+repr(changes[changetime])) # DEBUG
      
      dayvalue = changes[changetime]
      # compute increasing and descreasing
      if dayvalue > previoussum:
        reopened = dayvalue - previoussum
      else:
        closed = previoussum - dayvalue
      
      # simplify visualization for integer values
      if (dayvalue % 1 == 0) and (reopened % 1 == 0) and (closed % 1 == 0):
        dayvalue = int(dayvalue)
        reopened = int(reopened)
        closed = int(closed)
      
      previoussum = dayvalue
      
      if firstday <= changetime and changetime <= lastday :
        if changetime < today:
          todayid += 1
        
        if maxTicketnumberComplete < dayvalue: # save the largest number
          maxTicketnumberComplete = dayvalue
        self.macroenv.tracenv.log.debug('changetime: '+str(self.getDayString(firstday)  )+' <= '+str(self.getDayString(changetime)  )+' <= '+str(self.getDayString(lastday)) )
        #trDays(tag.th(changeday))
        changetimeprint = self.getSegmentString(changetime)
        trDays(tag.th(changetimeprint))
        #trDaysAxis(tag.th(str(changetime)+"\n("+self.getDayString(changetime)+")"))
        trDaysAxis(tag.th(changetimeprint))
        trOpenTickets(tag.td(str(dayvalue)))
        #trOpenTickets(tag.td(ticketnumberFlexible))
        trClosedTickets(tag.td(str(closed)))
        trReopenedTickets(tag.td(str(reopened)))
      
      # bug exists in javascript rendering if all values are zeor
    self.macroenv.tracenv.log.debug("maxTicketnumberComplete: "+str(maxTicketnumberComplete))
    if int(maxTicketnumberComplete) == 0:
      self.macroenv.tracenv.log.warning("nothing to show: %s" % (repr(self.macroenv.macrokw)))
      return tag.div("nothing to show, choose select at least one ticket or a field containing at one point in time a value higher than zero.", class_='ppwarning')
    elif int(maxTicketnumberComplete) < 3:
      maxTicketnumberComplete = 3
      
      #inner(tag.td(changeday)) # TEST
      #inner(tag.td(ticketnumberComplete))# TEST
      #inner(tag.td(ticketnumberFlexible))# TEST
      #inner(tag.td( 'closed at this date: ' ))# TEST
      #inner(tag.td( str(closed) ))# TEST
      #outer2(inner)# TEST
    
    outer2(tag.thead(trDays))
    outer2(tag.tfoot(trDaysAxis))
    outer2(tag.tbody(trOpenTickets, trClosedTickets, trReopenedTickets ))
    
    
    holderid = self.getNameOfRenderFrame()+'holder'
    (label1,label2) = self.getLabel()
    
    
    # configuration of renderer
    frame(tag.div( maxTicketnumberComplete, class_ = 'maxTasks' ))
    frame(tag.div( self.width, class_ = 'width' ))
    frame(tag.div( self.height, class_ = 'height' ))
    frame(tag.div( label1, class_ = 'label1' ))
    frame(tag.div( label2, class_ = 'label2' ))
    frame(tag.div( todayid, class_ = 'today' )) # number of column with the current date
    frame(tag.div( holderid, class_ = 'holder' )) # where to put the chart in
    
    frame(outer2)
    outerframe = tag.div() # div as global container
    #outerframe(outer) # DEBUG
    outerframe(frame)
    outerframe(tag.div( id = holderid ), style="border-width:1px" )
    return outerframe


class BurndownChartTickets( BurndownChart ):
  '''
    default field value is the number of open/closed tickets
  '''
  def __init__(self, macroenv ):
    BurndownChart.__init__(self, macroenv)
  

