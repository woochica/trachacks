# -*- coding: utf-8 -*-
"""
Maintain synchronization of Trac tickets in Salesforce.  Trac tickets are
reflected by the Salesforce custom object, Ticket__c and Comment__c.  
Ticket__c objects are linked to Cases via M2M relationship provided by
the CaseTicketLink__c custom object.  Even though this is a M2M relation,
Trac's uses a custom text field for the Case number, so it's essentially 
many-to-one.  

Comment__c objects are related to Ticket__c objects via the link custom
object, TicketCommentLink__cc.  The related lists layouts are modified to
display the related object fields rather then the object id.

You need the "tracrpc" component installed and enabled for this 
plugin to work.  You also need to add a custom field, "case_number",
as shown below.

This file gets copied to the "plugins" directory of the trac project.

Example settings in trac.ini are:

[components]
tracrpc.* = enabled
ticket2sforce.* = enabled
ticketvalidator.* = enabled

[ticket2sforce]
username = yourSFusername
password = yourSFpasswd
sectoken = yourSFsecurityToken
wsdl = partner.wsdl

[ticket-custom]
case_number = text
case_number.label = Case Number

[ticketvalidator]
new.required = case_number

You will need to install the following Salesforce project
artifacts using either the Eclipse SForce plugin or the 
ant-based migration tool.

src/layouts/Case-Case Layout.layout
src/layouts/Comment__c-Comment Layout.layout
src/layouts/Ticket__c-Ticket Layout.layout
src/layouts/TicketCommentLink__c-TicketCommentLink Leyout.layout
src/objects/Ticket__c.object
src/objects/Comment__c.object
src/objects/CaseTicketLink__c.object
src/objects/TicketCommentLink__c.object

Author: Chris Wolf   cw10025 AT gmail
"""
import re
import sys, datetime
from genshi.builder import tag
from trac.core import *
from trac.core import ComponentManager
from trac.ticket.api import ITicketChangeListener
from trac.ticket.api import ITicketManipulator
from sforce.partner import SforcePartnerClient

class Ticket2SForce(Component):
  implements(ITicketManipulator, ITicketChangeListener)
  
  # map Trac ticket field names to Salesforce custom object Ticket__c field names 
  fieldMap = \
    {'id': 'Trac_Ticket_Id__c',
     'status': 'Status__c',
     'summary': 'Summary__c',
     'reporter': 'Reporter__c',
     'cc': 'Cc__c',
     'changetime': 'Last_Update_Time__c',
     'time': 'Time__c',
     'description': 'Description__c',
     'component': 'Component__c',
     'priority': 'Priority__c',
     'owner': 'Owner_cc',
     'version': 'Version__c',
     'milestone': 'Milestone__c',
     'keywords': 'Keywords__c',
     'type': 'Type__c'}
      
  def connect2SForce(self):
    self.env.log.debug('--- Called connect2SForce: %s, %s, %s, %s' % \
      (self.username, self.password, self.sectoken, self.wsdlPath))
    self.sf = SforcePartnerClient(self.wsdlPath)
    self.sf.login(self.username, self.password, self.sectoken)
    #self.env.log.debug('**** SessionId: ' + self.sf._sessionHeader.sessionId)
    
  def __init__(self):
    self.env.log.debug('--------------- Ticket2SForce init')
    self.wsdlPath = 'file://' + self.env.config.getpath('ticket2sforce', 'wsdl')
    self.username = self.config.get('ticket2sforce', 'username', '')
    self.password = self.config.get('ticket2sforce', 'password', '')
    self.sectoken = self.config.get('ticket2sforce', 'sectoken', '')
    self.delete_closed_ticket = self.config.get('ticket2sforce', 'delete_closed_ticket', 'false')
    self.connect2SForce()

  def prepare_ticket(self, req, ticket, fields, actions):
    """Not currently called, but should be provided for future
    compatibility.
    """

  def validate_ticket(self, req, ticket):
    """Validate a ticket after it's been populated from user input.
    Must return a list of `(field, message)` tuples, one for each problem
    """
    self.env.log.debug("******** Called validate_ticket ***")
    caseNumber = ticket['case_number']
    if caseNumber == None or len(caseNumber) < 1:
      return [('case_number', 'case_number is required')]
    
    qstr = u"select Id, CaseNumber from Case where CaseNumber = '%s'" \
      % (caseNumber)
    result = self.sf.query(qstr)
    if result.size < 1:
      return [('case_number', 'case_number is not in the configured Org')]

    self.caseId = result.records[0].Id
    return []
  
  def createCaseTicketLink(self, caseId, ticketId):
    """
      Create M2M link Case <==> Ticket
    """
    link           = self.sf.generateObject('CaseTicketLink__c') 
    link.Case__c   = caseId
    link.Ticket__c = ticketId
    result         = self.sf.create(link)
    
    if result.success != True:
      msg = "Error: Can't create CaseTicketLink record for %s, result was %s" \
        % (str(link), result)      
      raise Exception(msg)
    return result
   
  def createComment(self, author, comment_text):
    """
    Create Comment_cc and link object, to be linked to Ticket__cc
    """
    comment             = self.sf.generateObject('Comment__c')
    comment.Author__c   = author
    comment.Comment__c  = comment_text
    result              = self.sf.create(comment)
    
    if result.success != True:
      msg = "Error: Can't create Comment record for %s, result was %s" \
        % (str(link), result)      
      raise Exception(msg)
    return result   
      
  def createTicketCommentLink(self, ticketId, commentId):
    """
      Create M2M link Ticket <==> Comment
    """
    link            = self.sf.generateObject('TicketCommentLink__c') 
    link.Ticket__c  = ticketId
    link.Comment__c = commentId
    result          = self.sf.create(link)
    
    if result.success != True:
      msg = "Error: Can't create TicketCommentLink record for %s, result was %s" \
        % (str(link), result)      
      raise Exception(msg)
    return result   
  
  def createTicket(self, record):
    """
      Create a Ticket__c record, associated with the ticket in Trac
    """
    ticket                      = self.sf.generateObject('Ticket__c')
    ticket.Trac_Ticket_Id__c    = record.id
    ticket.Name                 = record.id
    ticket.Status__c            = record['status']
    ticket.Summary__c           = record['summary']
    ticket.Reporter__c          = record['reporter']
    ticket.Cc__c                = record['cc']
    ticket.Last_Update_Time__c  = record['changetime'].isoformat()
    ticket.Time__c              = record['time'].isoformat()
    ticket.Description__c       = record['description']
    ticket.Component__c         = record['component']
    ticket.Priority__c          = record['priority']
    ticket.Owner__c             = record['owner']
    ticket.Version__c           = record['version']
    ticket.Milestone__c         = record['milestone']
    ticket.Keywords__c          = record['keywords']
    ticket.Type__c              = record['type']
    result                      = self.sf.create(ticket)

    if result.success != True:
      msg = "Error: Can't create Ticket record for %s, result was %s" \
        % (str(record), result)      
      raise Exception(msg)

    return result

  def updateTicket(self, ticketId, ticket, old_values):
    """
      Update existing Ticket - only fields that changed
    """
    
    fieldList = ','.join([Ticket2SForce.fieldMap[fld] for fld in old_values.iterkeys()]) 
    sfTicket = self.sf.retrieve(fieldList, 'Ticket__c', ticketId)
    for fld in old_values.iterkeys():
      sfTicket[Ticket2SForce.fieldMap[fld]] = ticket.values[fld]
    
    result = self.sf.update(sfTicket)

    if result.success != True:
      msg = "Error: Can't update Ticket record for %s, result was %s" \
        % (str(sfTicket), result)      
      raise Exception(msg)

    return result  

  def create_sfticket(self, ticket):
    self.env.log.debug('--------------- create_sfticket')
    self.env.log.debug(ticket['priority'])
    result = self.createTicket(ticket)
    ticketId = result.id
    result = self.createCaseTicketLink(self.caseId, ticketId)
    
  def change_sfticket(self, ticket, comment, author, old_values):
    self.env.log.debug('--------------- change_sfticket')
    qstr = u"select Id, Trac_Ticket_Id__c from Ticket__c where Trac_Ticket_Id__c = '%s'" \
      % (ticket.id)
    result = self.sf.query(qstr)
    if result.size < 1:    
      msg = "Error: Can't locate Ticket record for %s, result was %s" \
        % (str(ticket), result)      
      raise Exception(msg)
          
    ticketId = result.records[0].Id
    ticketNumber = result.records[0].Trac_Ticket_Id__c
    
    if len(comment) > 0:
      result = self.createComment(author, comment)   
      commentId = result.id
      result = self.createTicketCommentLink(ticketId, commentId)
    if len(old_values) > 0:
      self.updateTicket(ticketId, ticket, old_values)   
        
  def complete_sfticket(self, ticket):
    self.env.log.debug('--------------- complete_sfticket')
    #self.rtm_instance.complete_task(ticket)

  # ITicketChangeListener
  def ticket_created(self, ticket):
    #self.env.log.debug("*** ticket: %d: %s %s\n" % (ticket.id, type(ticket.values['changetime']), str(ticket.values)))
    #for key, value in ticket.values.iteritems():
    #   self.env.log.debug("    %s: %s\n" % (key, value))
    self.create_sfticket(ticket)

  def ticket_changed(self, ticket, comment, author, old_values):
    self.env.log.debug('################ ticket_changed')
    self.env.log.debug('>>>>>>>>>> ' + comment)
    self.env.log.debug(ticket['status'])
    self.env.log.debug(old_values)
    #for key, value in old_values.iteritems():
    #  self.env.log.debug("    %s: %s\n" % (key, value))
      
    for key, value in ticket.values.iteritems():
      self.env.log.debug("    %s: %s" % (key, value))
      
    if ticket['status'] == 'closed' and old_values['status'] != 'closed':
      self.complete_sfticket(ticket)
    else:
      self.change_sfticket(ticket, comment, author, old_values)

  def ticket_deleted(self, ticket):
    self.env.log.debug('################ ticket_deleted')
    self.complete_sfticket(ticket)
