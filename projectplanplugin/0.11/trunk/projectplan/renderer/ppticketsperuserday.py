# -*- coding: utf-8 -*-

'''
  ALPHA
  TODO: extend the statistics within the footer of the table
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

class TicketsPerUserDay(RenderImpl):
  '''
    render a table
  '''
  fielddefault = 'status'
  weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su' ]
  FRAME_LABEL = 'Table: Tickets of User per Day'
  
  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
    
    segments = self.macroenv.macrokw.get('segments')
    if segments == None:
      self.segments = []
    else:
      self.segments = [ self.parseTimeSegment(s.strip()) for s in segments.split(';') ] 
    
    
    rows = self.macroenv.macrokw.get('rows') # standard parameter
    rowtype = self.macroenv.macrokw.get('rowtype') # standard parameter
    
    # backward compatibility
    if rows == None :
      rows = self.macroenv.macrokw.get('owners') # left for legacy reasons
      rowtype = 'owner' # left for legacy reasons
    
    self.rowtype = rowtype
    if rows == None :
      self.rows = []
    else:
      self.rows = [ o.strip() for o in rows.split(';') ] 
    
    cssclass = self.macroenv.macrokw.get('cssclass')
    if cssclass == None:
      self.cssclass = 'blacktable' # fallback
    else:
      self.cssclass = cssclass.strip()
    
    
    showsummary = self.macroenv.macrokw.get('summary')
    self.showsummarypiechart = False
    
    if showsummary == None:
      pass # fallback
    else:
      showsummary = showsummary.lower()
      if showsummary == 'chart' : 
        self.showsummarypiechart = True # default
      elif showsummary == 'chart:pie':
        self.showsummarypiechart = True
      else:
        pass

    self.statistics_class = '' # default
    try:
      #self.macroenv.tracenv.log.error('fields: '+self.macroenv.macrokw.get('statistics'))
      tmp = self.macroenv.macrokw.get('statistics').split('/')
      self.statistics_fields = []
      for field in tmp:
        try:
          if field != None and field != '' and field.strip() != '':
            self.statistics_fields.append(field.strip())
        except:
          pass
      self.statistics_class = 'pptableticketperday'
    except Exception,e:
      self.macroenv.tracenv.log.warning(repr(e))
      self.statistics_fields = [] # fallback
    
    
    self.isShowAggregatedTicketState = self.macroenv.get_bool_arg('showaggregatedstate', False)
    

  def isSummary( self ):
    return self.showsummarypiechart or False # add other values
  
  def showAggregatedTicketState( self ):
    return self.isShowAggregatedTicketState or False

  def getHeadline( self ):
    title = self.getTitle()
    if title != None:
      return('%s: %s' % (self.FRAME_LABEL,title))
    else:
      return('%s' % (self.FRAME_LABEL,))

  def render_statistics(self,ticketlist):
    # fallback if preconditions are not holding
    if len(ticketlist) == 0 or self.statistics_fields == []:
      return tag.span()
    
    # create a new map 
    statistics_values = {}
    for field in self.statistics_fields:
      statistics_values[field] = 0
    
    # map containing titles
    field_titles = {}
    for field in self.statistics_fields:
      field_titles[field] = 'sum of "%s"' % (field,)
    
    # summarize the field values of each ticket
    html = tag.div()
    for ticket in ticketlist:
      for field in self.statistics_fields:
        try:
          statistics_values[field] += int(ticket.getfield(field))
        except:
          field_titles[field] = '"%s" could not be parsed to number' % (field,)

    # create html construct
    separator = ''
    for field in self.statistics_fields:
      html(separator, tag.span('%s' % (statistics_values[field],), title=field_titles[field]) )
      separator = '/'

    return tag.div(html, class_='pptableticketperdaystatistics')

  def render(self, ticketset):
    '''
      Generate HTML List
      TODO: improve computation of ticket set
    '''
    orderedtickets = {}
    field = 'due_close'
    weekdays = ['PLACEHOLDER', 'Mo','Tu','We','Th','Fr','Sa','Su']
    
    r = ''
    div = tag.div()
    
    div(class_=self.cssclass+' projectplanrender' )
    
    # check for missing parameters 
    missingparameter = False
    if self.rows == [] :
      div(tag.div('Missing parameter "rows": use a semicolon-separated list to input the "'+self.rowtype+'".', class_='ppwarning')) 
      missingparameter = True
    if self.rowtype == None or  str(self.rowtype).strip() == '':
      div(tag.div('Missing parameter "rowtype": specifies the ticket attribute that should be showed.', class_='ppwarning')) 
      missingparameter = True
    if self.segments == [] :
      div(tag.div('Missing parameter: use a semicolon-separated list to input the "segments".', class_='ppwarning'))
      missingparameter = True
    if missingparameter:
      return div
    
    # init the matrix
    for segment in self.segments :
      orderedtickets[segment] = {}
      for o in self.rows:
        orderedtickets[segment][o] = []
    
    # fill up matrix
    self.macroenv.tracenv.log.debug('number of tickets: '+str(len(ticketset.getIDList())) )
    for tid in ticketset.getIDList():
      try:
        ticket = ticketset.getTicket(tid)
        orderedtickets[ticket.getfield(field)][ticket.getfield(self.rowtype)].append(ticket)
      except Exception,e:
        self.macroenv.tracenv.log.debug('fill up matrix: #'+str(tid)+' '+repr(e))
        pass
    
    calendar = {}
    counttickets = {}
    currentDate = datetime.date.today()
    
    self.macroenv.tracenv.log.debug(repr(orderedtickets))
    table = tag.table( class_="data pptableticketperday" , border = "1", style = 'width:auto;')
    
    # standard values
    mystyle_org = ''
    mytitle_org = ''
    myclass_org = '' 
    
    # table header
    tr = tag.tr()
    tr(tag.th(tag.h4(self.rowtype)))
    # TODO: add today css class
    for segment in self.segments:
      mystyle = mystyle_org
      mytitle = mytitle_org
      myclass = myclass_org
      try:
        consideredDate = self.getDateOfSegment(segment)
        calendar[segment] = {}
        calendar[segment]['isocalendar'] = consideredDate.isocalendar()
        calendar[segment]['date'] = consideredDate
        subtitle = weekdays[calendar[segment]['isocalendar'][2]] + ', week '+str(calendar[segment]['isocalendar'][1])
        if consideredDate == currentDate:
          myclass = 'today' # overwrite
      except Exception,e:
        self.macroenv.tracenv.log.error(str(e)+' '+segment)
        calendar[segment]['isocalendar'] = (None, None, None)
        calendar[segment]['date'] = None
        subtitle = "--"
        mystyle = 'color:#000;'
        mytitle = 'date could not be resolved'
      tr(tag.th(tag.h4(segment, class_ = myclass ), tag.h5( subtitle, style = mystyle, title = mytitle, class_ = myclass  ))) 
      counttickets[segment] = 0
    if self.showsummarypiechart:
      tr(tag.th(tag.h4('Summary', class_ = myclass_org ), tag.h5( 'of all tickets', style = mystyle_org, title = mytitle_org, class_ = myclass_org ))) 
    table(tag.thead(tr)) # Summary
    
    self.macroenv.tracenv.log.debug('tickets in table: '+repr(orderedtickets))
    
    
    # table body
    tbody = tag.tbody()
    counter=0
    
    for o in self.rows:
      if counter % 2 == 1:
        class_ = 'odd'
      else:
        class_ = 'even'
      counter += 1
      tr = tag.tr(class_ = class_)
      
      tr( tag.td(tag.h5(tag.a( o, href=self.macroenv.tracenv.href()+('/query?%s=%s&order=status' % (self.rowtype,o,)) )))) # query owner's tickets
      countStatus = {} # summarize the status of a ticket 
      for segment in self.segments:
        class_ = ''
        if calendar[segment]['date'] == currentDate: # Today
          class_ = 'today'
        elif calendar[segment]['isocalendar'][2] == 6: # Saturday
          class_ = 'saturday'
        elif calendar[segment]['isocalendar'][2] == 7: # Sunday
          class_ = 'sunday'
        td_div = tag.div()
        
        
        # only show the highlight, if the date is in the past
        color_class = ''
        if  self.showAggregatedTicketState()  and  calendar[segment]['date'] < currentDate:
          # determine color 
          state_new = 1
          state_work = 2
          state_done = 3
          state_none = 4
          
          state_progess = state_none
          
          for ticket in orderedtickets[segment][o]:
            status = ticket.getfield('status')
            if status in ['in_QA','closed'] and state_progess >= state_done:
              state_progess = state_done
            elif status in ['in_work','assigned','infoneeded'] and state_progess >= state_work:
              state_progess = state_work
            elif status in ['new','infoneeded_new'] and state_progess >= state_new:
              state_progess = state_new
          
          color_class =  { # switch/case in Python style
            state_none: '',
            state_new: 'bar bar_red',
            state_work: 'bar bar_blue',
            state_done: 'bar bar_green'
          }.get(state_progess, '')
        
        
        
        for ticket in orderedtickets[segment][o]:
          counttickets[segment] += 1
          td_div(tag.div( tag.span(self.createTicketLink(ticket), class_ = 'ticket_inner') ) )
          
          if ticket.getfield('status') in countStatus.keys(): # count values
            countStatus[ticket.getfield('status')] += 1
          else:
            countStatus[ticket.getfield('status')] = 1
        
        #tr(tag.td( tag.div( td_div, style = 'border-left:3px solid %s;' % (color) ) ) )
        tr(tag.td( tag.div( td_div ), self.render_statistics(orderedtickets[segment][o]), class_ = '%s %s %s' % (color_class, class_, self.statistics_class)  ) )
      if self.showsummarypiechart:
        tr(tag.td(tag.img(src=self.createGoogleChartFromDict('ColorForStatus', countStatus)))) # Summary
      tbody(tr)
    table(tbody)
    
    countTickets = 0
    tfoot = tag.tfoot()
    tr = tag.tr()
    tr(tag.td(tag.h5(self.rowtype+': '+str(len(self.rows)))))
    for segment in self.segments:
      tr(tag.td(tag.h5(str(counttickets[segment])+' tickets')))
      countTickets += counttickets[segment]
    if self.showsummarypiechart:
      tr(tag.td(tag.h5(str(str(countTickets))+' tickets'))) # Summary
    tfoot(tr)
    table(tfoot)
    
    div(table)
    return div




