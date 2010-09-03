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
    
    
    owners = self.macroenv.macrokw.get('owners')
    if owners == None :
      self.owners = []
    else:
      self.owners = [ o.strip() for o in owners.split(';') ] 
    
    cssclass = self.macroenv.macrokw.get('cssclass')
    if cssclass == None:
      self.cssclass = 'blacktable' # fallback
    else:
      self.cssclass = cssclass.strip()
    

  def getHeadline( self ):
    title = self.getTitle()
    if title != None:
      return('%s: %s' % (self.FRAME_LABEL,title))
    else:
      return('%s' % (self.FRAME_LABEL,))
 
  def render(self, ticketset):
    '''
      Generate HTML List
    '''
    orderedtickets = {}
    field = 'due_close'
    owner = 'owner'
    weekdays = ['PLACEHOLDER', 'Mo','Tu','We','Th','Fr','Sa','Su']
    
    r = ''
    div = tag.div()
    
    div(class_=self.cssclass+' projectplanrender' )
    #self.owners = ['somebody', 'anonymous' ]
    #self.segments = ['08/01/2010', '09/01/2010', '10/01/2010','11/01/2010', '16/01/2010']
    
    # check for missing parameters 
    missingparameter = False
    if self.owners == [] :
      div(tag.div('Missing parameter: use a semicolon-separated list to input the "owners".', class_='ppwarning'))
      missingparameter = True
    if self.segments == [] :
      div(tag.div('Missing parameter: use a semicolon-separated list to input the "segments".', class_='ppwarning'))
      missingparameter = True
    if missingparameter:
      return div
    
    # init the matrix
    for segment in self.segments :
      orderedtickets[segment] = {}
      for o in self.owners:
        orderedtickets[segment][o] = []
    
    # fill up matrix
    for tid in ticketset.getIDList():
      try:
        ticket = ticketset.getTicket(tid)
        #orderedtickets[ticket.getfield(field)][ticket.getfield(owner)].append(tag.a(href=self.env.href.wiki(str(tid)), str(tid)))
        orderedtickets[ticket.getfield(field)][ticket.getfield(owner)].append(tid)
      except Exception,e:
        self.macroenv.tracenv.log.warning(repr(e))
        pass
    
    calendar = {}
    counttickets = {}
    currentDate = datetime.date.today()
    
    self.macroenv.tracenv.log.debug(repr(orderedtickets))
    table = tag.table( class_="data" , border = "1", style = 'width:auto;')
    
    # table header
    tr = tag.tr()
    tr(tag.th('Ticket Owner'))
    # TODO: add today css class
    for segment in self.segments:
      mystyle = ''
      mytitle = ''
      myclass = ''
      try:
        consideredDate = self.getDateOfSegment(segment)
        calendar[segment] = {}
        calendar[segment]['isocalendar'] = consideredDate.isocalendar()
        calendar[segment]['date'] = consideredDate
        subtitle = weekdays[calendar[segment]['isocalendar'][2]] + ', week '+str(calendar[segment]['isocalendar'][1])
        if consideredDate == currentDate:
          self.macroenv.tracenv.log.error('th.today')
          myclass = 'today'
        else:
          self.macroenv.tracenv.log.error('NO th.today')
        #tr(tag.th(tag.h4(segment), tag.h5( subtitle))) # week day and number
      except Exception,e:
        self.macroenv.tracenv.log.error(str(e)+' '+segment)
        calendar[segment]['isocalendar'] = (None, None, None)
        calendar[segment]['date'] = None
        subtitle = "--"
        mystyle = 'color:#000;'
        mytitle = 'date could not be resolved'
        #tr(tag.th(tag.h4(segment), tag.h5( subtitle, style = 'color:#000;', title = 'date could not be resolved' ))) # HACK
      tr(tag.th(tag.h4(segment, class_ = myclass ), tag.h5( subtitle, style = mystyle, title = mytitle, class_ = myclass  ))) 
      counttickets[segment] = 0
    table(tag.thead(tr))
    
    # table body
    tbody = tag.tbody()
    counter=0
    for o in self.owners:
      if counter % 2 == 1:
        class_ = 'odd'
      else:
        class_ = 'even'
      counter += 1
      tr = tag.tr(class_ = class_)
      
      tr( tag.td(tag.h4(o)))
      for segment in self.segments:
        class_ = ''
        if calendar[segment]['date'] == currentDate: # Today
          class_ = 'today'
        elif calendar[segment]['isocalendar'][2] == 6: # Saturday
          class_ = 'saturday'
        elif calendar[segment]['isocalendar'][2] == 7: # Saturday
          class_ = 'sunday'
        td = tag.td(class_ = class_)
        
        for tid in orderedtickets[segment][o]:
          counttickets[segment] += 1
          #td(tag.a(str(tid),href=self.macroenv.tracenv.href.ticket(tid) ), ' ' )
          #td(tag.a(str(tid),href='http://www.google.de' ))
          td(tag.span(tag.a('#'+str(tid), href=self.macroenv.tracenv.href.ticket(tid) ), class_ = 'ticket_inner') )
          td(' ')
        #td(title='tickets of '+o+' at '+segment)
        tr(td)
      tbody(tr)
    table(tbody)
    
    tfoot = tag.tfoot()
    tr = tag.tr()
    tr(tag.td(tag.h5(str(len(self.owners))+' owners')))
    for segment in self.segments:
      tr(tag.td(tag.h5(str(counttickets[segment])+' tickets')))
    tfoot(tr)
    
    table(tfoot)
    
    div(table)
    return div




