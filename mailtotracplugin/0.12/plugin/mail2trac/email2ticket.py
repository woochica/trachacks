"""
Trac email handlers having to do with tickets
"""

import os, sys
import re
from datetime import datetime


from mail2trac.email2trac import EmailException
from mail2trac.interface import IEmailHandler
from mail2trac.utils import add_attachments
from mail2trac.utils import emailaddr2user
from mail2trac.utils import get_body_and_attachments
from mail2trac.utils import strip_res
from trac.core import *
from trac.mimeview.api import KNOWN_MIME_TYPES
from trac.config import Option
from trac.perm import PermissionSystem
from trac.ticket import Ticket
from trac.ticket.api import TicketSystem
from trac.ticket.notification import TicketNotifyEmail
from trac.ticket.web_ui import TicketModule
from trac.util.datefmt import to_datetime, utc


### email handlers


##-----------------------------------------------------------------------------
## general functions



##-----------------------------------------------------------------------------
## ticket creation 


class EmailToTicket(Component):
    """create a ticket from an email"""
    implements(IEmailHandler)


    possibleFields = ['owner', 'type', 'status', 'priority', 'milestone', 'component', 'version', 'resolution', 'keywords', 'cc', 'time', 'changetime']

    ### methods for IEmailHandler

    # we detect a creation because the subject is "create: title"
    def match(self, message):
        regexp = r' *create *:'
        return bool(re.match(regexp, message['subject'].lower()))


    
    def invoke(self, message, warnings):
        """make a new ticket on receiving email"""


        # local warnings
        _warnings = []

        # get the ticket reporter
        reporter = self._reporter(message)
        # get the description and attachments
        mailBody, attachments = get_body_and_attachments(message)
        if mailBody is None:
            mailBody = ''


        # get the ticket fields
        fields = self._fields(unicode(message['subject'], "utf8"), mailBody, _warnings, reporter=reporter)

        # inset items from email
        ticket = Ticket(self.env)
        for key, value in fields.items():
            ticket.values[key] = value



        # fill in default values
        for field in ticket.fields:
            name = field['name']
            if name not in fields:
                option = 'ticket_field.%s' % name
                if self.env.config.has_option('mail', option):
                    ticket.values[name] = self.env.config.get('mail', option)
                else:
                    try:
                        value = ticket.get_value_or_default(name) or ''
                    except AttributeError: # BBB
                        value = ''
                    if value is not None:
                        ticket.values[name] = value


        # create the ticket
        ticket.insert()

        # add attachments to the ticket
        add_attachments(self.env, ticket, attachments)

        # do whatever post-processing is necessary
        self.post_process(ticket)

        # add local warnings
        if _warnings:
            warning = """A ticket has been created but there is a problem:\n\n%s\n\nPlease edit your ticket by going here: %s""" % ('\n\n'.join([' - %s' % warning for warning in _warnings]), self.env.abs_href('ticket', ticket.id))
            warnings.append(warning)

    ### internal methods



    #return the fields present in the bodymail, and the body mail clean (witout this fields)
    def _get_in_body_fields(self, mailBody) :
        # #end is the end of what must be read in a body mail.
        end = mailBody.lower().find('#end')
        if end <> -1 :
            mailBody = mailBody[:end]
        
        mailBody.strip()

        res = {}

        # we look for all possible fields
        for fieldName in self.possibleFields : 
            matched = re.search(r'(?P<all>^[ \t]*\#[ \t]*%s[ \t]*:[ \t]*(?P<value>.*?))$'%fieldName, mailBody, re.IGNORECASE | re.MULTILINE)
            if matched :
                res[fieldName] = matched.group('value').strip()


        #we clean the body mail of "^ *#
        #manage the problem of 'is this field declaration the last line (without \n at end)?'
        if mailBody[0] <> '\n' : mailBody = '\n' + mailBody 
        mailBody = re.sub(r'\n\s*#.*', "", mailBody, re.MULTILINE)
        
        return mailBody.strip(), res




    def _reporter(self, message):
        """return the ticket reporter or updater"""
        user = emailaddr2user(self.env, message['from'])
        # check permissions
        perm = PermissionSystem(self.env)
        if not perm.check_permission('MAIL2TICKET_CREATE', user) : # None -> 'anoymous'
            raise EmailException("%s does not have MAIL2TRAC_CREATE permissions" % (user or 'anonymous'))
    
        reporter = user or message['from']
        return reporter

    def _fields(self, subject, mailBody, warnings, **fields):

        # effectively the interface for email -> ticket

        mailBody, inBodyFields = self._get_in_body_fields(mailBody)
        #clean subject : the summary is the message subject, except the 'create:', so we take it after the first ':'
        subject = subject[subject.find(':')+1:].strip()
        fields.update(dict(description = mailBody,
                           summary = subject,
                           status='new',
                           resolution=''), **inBodyFields)
        
        return fields

    def post_process(self, ticket):
        """actions to perform after the ticket is created"""

        # ticket notification
        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket)
    

##-----------------------------------------------------------------------------
## ticket update



class ReplyToTicket(Component):
    
    implements(IEmailHandler)

    possibleFields = ['type', 'priority', 'milestone', 'component', 'version', 'keywords', 'cc']
    action_aliases = {'fixed' : {'action' : 'resolve' , 'value' : 'fixed'},
                      'duplicate' : {'action' : 'resolve' , 'value' : 'duplicate'},
                      'wontfix' : {'action' : 'resolve' , 'value' : 'wontfix'},
                      'invalid' : {'action' : 'resolve' , 'value' : 'invalid'},
                      }

    
    def match(self, message):
        self.ticket = self._ticket(message)
        return bool(self.ticket)

        
    def invoke(self, message, warnings):
        """reply to a ticket"""
        ticket = self.ticket
        reporter = self._reporter(message)
        # get the mailBody and attachments
        mailBody, attachments = get_body_and_attachments(message)
        if not mailBody:
            warnings.append("Seems to be a reply to %s but I couldn't find a comment")
            return message

        #go throught work

        ts = TicketSystem(self.env)
        tm = TicketModule(self.env)
        perm = PermissionSystem(self.env)
        # TODO: Deprecate update without time_changed timestamp
        mockReq = self._MockReq(perm.get_user_permissions(reporter), reporter)
        avail_actions = ts.get_available_actions(mockReq, ticket)

        mailBody, inBodyFields, actions = self._get_in_body_fields(mailBody, avail_actions, reporter)
        if inBodyFields or actions :
            # check permissions
            perm = PermissionSystem(self.env)
            #we have properties movement, cheking user permission to do so
            if not perm.check_permission('MAIL2TICKET_PROPERTIES', reporter) : # None -> 'anoymous'
                raise ("%s does not have MAIL2TICKET_PROPERTIES permissions" % (user or 'anonymous'))

        action = actions.keys()[0] if actions else None 
        controllers = list(tm._get_action_controllers(mockReq, ticket, action))
        all_fields = [field['name'] for field in ts.get_ticket_fields()]


        #impact changes find in inBodyFields
        for field in inBodyFields :
            ticket._old[field] = ticket[field]
            ticket.values[field] = inBodyFields[field]
            mockReq.args[field] = inBodyFields[field]
        if action : 
            mockReq.args['action_%s_reassign_owner' % action] = ticket['owner']



        mockReq.args['comment'] = mailBody
        mockReq.args['ts'] = datetime.now()#to_datetime(None, utc)


        mockReq.args['ts'] = str(ticket.time_changed)
        
        changes, problems = tm.get_ticket_changes(mockReq, ticket, action)
        valid = problems and False or tm._validate_ticket(mockReq, ticket)

        tm._apply_ticket_changes(ticket, changes)


        # add attachments to the ticket
        add_attachments(self.env, ticket, attachments)

        ticket.save_changes(reporter, mailBody)
        
        for controller in controllers:
            controller.apply_action_side_effects(mockReq, ticket, action)
            # Call ticket change listeners
        for listener in ts.change_listeners:
            listener.ticket_changed(t, comment, author, ticket._old)

        tn = TicketNotifyEmail(self.env)
        tn.notify(ticket, newticket=0, modtime=ticket.time_changed)


    #use a Mock Request to manage correctly permission throught ticketSystem

    class _MockReq() :

        permissions = []
        args = {}
        chrome = {'warnings' : [] }
        
        def __init__(self, permissions, reporter) :
            self.permissions = [ x for x in permissions if permissions[x] ]
            self.fields = {}
            self.authname = reporter

        def perm(self, any) :
            return self.permissions



    ### internal methods

    def _ticket(self, message):
        """
        return a ticket associated with a message subject,
        or None if not available
        """
        

        # get and format the subject template
        subject_template = self.env.config.get('notification', 'ticket_subject_template')
        prefix = self.env.config.get('notification', 'smtp_subject_prefix')
        subject_template = subject_template.replace('$prefix', 'prefix').replace('$summary', 'summary').replace('$ticket.id', 'ticketid')
        subject_template_escaped = re.escape(subject_template)

        # build the regex
        subject_re = subject_template_escaped.replace('summary', '.*').replace('ticketid', '([0-9]+)').replace('prefix', '.*')

        # get the real subject
        subject = strip_res(message['subject'])
        # see if it matches the regex
        match = re.match(subject_re, subject)
        if not match:
            return None

        # get the ticket
        ticket_id = int(match.groups()[0])
        #try:
        ticket = Ticket(self.env, ticket_id)
        #except:
        #    return None
        return ticket

    def _reporter(self, message):
        """return the ticket updater"""
        user = emailaddr2user(self.env, message['from'])
        # check permissions
        perm = PermissionSystem(self.env)
        if not perm.check_permission('MAIL2TICKET_COMMENT', user) : # None -> 'anoymous'
            raise EmailException("%s does not have MAIL2TRAC_COMMENT permissions" % (user or 'anonymous'))
        
        reporter = user or message['from']
        return reporter

    #return the fields present in the bodymail, and the body mail clean (witout this fields)
    def _get_in_body_fields(self, mailBody, avail_actions, reporter) :
        # #end is the end of what must be read in a body mail.
        end = mailBody.lower().find('#end')
        if end <> -1 :
            mailBody = mailBody[:end]
        
        mailBody.strip()

        res = {}

        # we look for all possible fields
        for fieldName in self.possibleFields : 
            matched = re.search(r'(?P<all>^[ \t]*\#[ \t]*%s[ \t]*:[ \t]*(?P<value>.*?))$'%fieldName, mailBody, re.IGNORECASE | re.MULTILINE)
            if matched :
                res[fieldName] = matched.group('value').strip()
                #manage the problem of 'is this field declaration the last line (without \n at end)?'

        #now we look at actions :
        actions = {}
        for action in avail_actions :
            #action with param
            matched = re.search(r'(?P<all>^[ \t]*\#[ \t]*%s[ \t]*:[ \t]*(?P<value>.*?))$'%action, mailBody, re.IGNORECASE | re.MULTILINE)
            if not matched :#try action without param
                matched = re.search(r'(?P<all>^[ \t]*\#[ \t]*%s[ \t]*[ \t]*(?P<value>.*?))$'%action, mailBody, re.IGNORECASE | re.MULTILINE)
            if matched :
                actions[action] = matched.group('value').strip()
                break #only one action #should emit a warning FIXME 


        #take care of aliases declared (the real action must be in avail_actions 

        if not actions : 
            for action in [ x for x in self.action_aliases if self.action_aliases[x]['action'] in avail_actions ] :
                matched = re.search(r'(?P<all>^[ \t]*\#[ \t]*%s[ \t]*[ \t]*$)'%action, mailBody, re.IGNORECASE | re.MULTILINE)
                if matched :
                    #we use values defined by action_aliases
                    actions[self.action_aliases[action]['action']] = self.action_aliases[action]['value']


        #we clean the body mail of "^ *#
        #manage the problem of 'is this field declaration the last line (without \n at end)?'
        if mailBody[0] <> '\n' : mailBody = '\n' + mailBody 
        mailBody = re.sub(r'\n\s*#.*', "", mailBody, re.MULTILINE)
        


        if actions :
            action = actions.keys()[0]
            value = actions[action]
            if action == 'reassign' :
                res['owner'] = value
                res['status'] = 'reassign'
            if action == 'resolve' :
                res['status'] = 'closed'
                res['resolution'] = value
            if action == 'accept' :
                res['status'] = 'accepted'
                res['owner'] = reporter
            if action == 'reopen':
                res['status'] = 'reopened'
                res['resolution'] = ''


        return mailBody.strip(), res, actions
