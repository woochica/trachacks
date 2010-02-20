# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestFilter #, IRequestHandler
from trac.ticket.query import *
from ppenv import PPConfiguration
from pputil import *
import re

class PPTicketViewTweak(Component):
  '''
    BETA: computes links on ticket dependency entries
  '''
  implements(ITemplateStreamFilter, IRequestFilter)
  
  field = None


  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      replace the dependency-field by links
    '''
    
    # stop if it is not a ticket
    if not req.path_info.startswith('/ticket/'):
      return stream
    
    self.field = PPConfiguration( self.env ).get('custom_dependency_field')
    
    dependencies = data['ticket'].values.get(self.field).strip()
    #dependencies = '1, 8; 2 y 3, 99,x' # test
    
    # TODO: replace this by a central method
    r = re.compile('[;, ]')
    deptickets = r.split(dependencies)
    
    nodeptickets = [ t for t in deptickets if str(t).strip() != "" and not isNumber(t) ]
    deptickets = [ t for t in deptickets if str(t).strip() != "" and isNumber(t) ]
    ticketsasstring = (','.join(deptickets))
    tickets = Query( self.env, constraints={ 'id' : [ticketsasstring] } ).execute( req )
    
    depwithlinks = ''
    sep = ''
    for dep in deptickets:
      if depwithlinks != '':
        sep = ', '
      else:
        sep = ''
      cssclass='ticket '
      try:
        ticket = [ t for t in tickets if str(t['id']) == dep ].pop()
        cssclass += ticket['status']+' ticket_inner' # need ticket_inner for mouseover effect
        # TODO: replace by absolute link
        depwithlinks = tag.span(depwithlinks, sep, tag.a( '#' + dep, href="./"+dep, class_ = cssclass ) )
      except Exception, e:
        cssclass += 'unknownticket'
        depwithlinks = tag.span(depwithlinks, sep, tag.a( '#' + dep , title="unknown ticket", class_ = cssclass) )
      
    cssclass = 'unknownticket'
    for nodep in nodeptickets :
      depwithlinks = tag.span(depwithlinks, sep, tag.a( nodep , title="no ticket id", class_ = cssclass) )
      sep = ', '
    
    stream |= Transformer('body/div[@id="main"]/div[@id="content"]/div[@id="ticket"]/table/tr/td[@headers="h_%s"]/text()' % self.field).replace(depwithlinks)
    
    return stream
 
 
  # IRequestFilter methods
  def pre_process_request(self, req, handler):
    return handler

  def post_process_request(self, req, template, data, content_type):
    '''
      add javascript and stylesheet to ticket view
    '''
    if req.path_info.startswith('/ticket/'):
      #tkt = data['ticket']
      addExternFiles(req)
    return template, data, content_type
 
 
