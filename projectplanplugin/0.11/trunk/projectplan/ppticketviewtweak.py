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
  fieldrev = None


  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      replace the dependency-field by links
    '''
    
    # stop if it is not a ticket view
    if not req.path_info.startswith('/ticket/') and not req.path_info.startswith('/newticket'):
      return stream
    
    self.field = PPConfiguration( self.env ).get('custom_dependency_field')
    self.fieldrev = PPConfiguration( self.env ).get('custom_reverse_dependency_field')
    try:
      dependencies = data['ticket'].values.get(self.field).strip()
      #dependencies = '1, 8; 2 y 3, 99,x' # test
    except:
      return stream
    
    current_ticket_id = data['ticket'].id
    
    # TODO: replace this by a central method
    r = re.compile('[;, ]')
    deptickets = r.split(dependencies)
    deptickets = [ t.replace('#', '')  for t in deptickets ]
    dependencies = self.createNormalizedTicketString(deptickets) # normalized
    
    blocking_tickets = self.getBlockingTickets( current_ticket_id ) 
    blocking_tickets_string = self.createNormalizedTicketString(blocking_tickets)
    
    nodeptickets = [ t for t in deptickets if str(t).strip() != "" and not isNumber(t) ]
    actualdeptickets = [ t for t in deptickets if str(t).strip() != "" and isNumber(t) ]
    
    depwithlinks = self.getTicketLinkList(req, actualdeptickets, nodeptickets)
    blocking_tickets_with_links = self.getTicketLinkList(req, blocking_tickets, [])
    
    self.env.log.debug('nodeptickets of '+str(current_ticket_id)+': '+repr(nodeptickets))
    self.env.log.debug('actualdeptickets of '+str(current_ticket_id)+': '+repr(actualdeptickets))
    self.env.log.debug('dependencies of '+str(current_ticket_id)+': '+repr(dependencies))
    
    # change summary block
    stream |= Transformer('body/div[@id="main"]/div[@id="content"]/div[@id="ticket"]/table/tr/td[@headers="h_%s"]/text()' % self.field).replace(depwithlinks)
    stream |= Transformer('body/div[@id="main"]/div[@id="content"]/div[@id="ticket"]/table/tr/td[@headers="h_%s"]/text()' % self.fieldrev).replace( blocking_tickets_with_links )
    
    # change fields
    stream |= Transformer('//*[@id="field-%s"]' % (self.field)).attr('value', dependencies)
    # TODO: blocking tickets field is still read only, should be changed to writable
    stream |= Transformer('//*[@id="field-%s"]' % (self.fieldrev)).attr('value', blocking_tickets_string).attr('readonly','readonly').attr('style','background-color:#EEEEEE') 
    
    # publish data that should be used by javascript
    stream |= Transformer('body/div[@id="main"]').prepend(
      tag.div( 
        tag.div( req.environ.get( 'ticketclosedf' ), id='ppDateFormat'),
        tag.div( 'field-'+self.field, id='ppDependenciesField'),
        tag.div( 'field-'+self.fieldrev, id='ppDependenciesReverseField'),
        id='ppTicketViewTweakConf'
    ))
    
    return stream
 
 
  # IRequestFilter methods
  def pre_process_request(self, req, handler):
    return handler

  def post_process_request(self, req, template, data, content_type):
    '''
      add javascript and stylesheet to ticket view
    '''
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      #tkt = data['ticket']
      addExternFiles(req)
    return template, data, content_type

  # helper methods
  def getBlockingTickets(self, ticket_id):
    '''
      calculate blocking tickets of the given ticket
      returns list of ticket ids (as string)
    '''
    sqlconstraint = '0'
    #sqlconstraint += " OR value = \"%s\"" % (ticket_id,) # lonely value
    #sqlconstraint += " OR value LIKE \"%% %s %%\"" % (ticket_id,) # middle
    #sqlconstraint += " OR value LIKE \"%% %s\"" % (ticket_id,) # left 
    #sqlconstraint += " OR value LIKE \"%s %%\"" % (ticket_id,) # right
    
    # TODO precondition: normalize dependencies field
    sqlconstraint += " OR value = \"%s\"" % (ticket_id,) # lonely value
    sqlconstraint += " OR value LIKE \"%% %s,%%\"" % (ticket_id,) # middle
    sqlconstraint += " OR value LIKE \"%% %s\"" % (ticket_id,) # left 
    sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
    
    #sqlconstraint += " OR value = \"#%s\"" % (ticket_id,) # lonely value
    #sqlconstraint += " OR value LIKE \"%% #%s %%\"" % (ticket_id,) # middle
    #sqlconstraint += " OR value LIKE \"%%,%s\"" % (ticket_id,) # left 
    #sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
    
    sql = "SELECT ticket FROM ticket_custom WHERE name = \"%s\" AND ( %s ) " % (self.field, sqlconstraint )
    db = self.env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sql)
    blocking_tickets = cursor.fetchall()
    ret = []
    for res in blocking_tickets:
      ret.append(str(res[0]))
    
    return ret

  def getTicketLinkList(self, req, deptickets, nodeptickets):
    '''
      translate ticket list into a div structure with ticket links
    '''
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
    
    return depwithlinks

  def createNormalizedTicketString( self, ticketlist ):
    '''
      remove all false entries in the list of tickets
    '''
    ticketstr = ', '.join([ t.strip().replace('#', '') for t in ticketlist  if str(t).strip() != "" ])
    return ticketstr
