"""
email2trac:
a pluggable email handler plugin for Trac
http://trac.edgewall.org
"""

import email
import email.Utils

import os
import sys, traceback
import urllib
import urllib2

from datetime import datetime
from interface import IEmailHandler
from utils import reply_body
from utils import reply_subject
from utils import send_email
from trac.core import *
from trac.env import open_environment

from trac.admin.api import IAdminCommandProvider #new command line
from trac.perm import IPermissionRequestor # new trac permission 



debug = True



# exception classes
class EmailException(Exception):
    """error exception when processing email messages"""

class AddressLookupException(Exception):
    """exception when try to match the email address for a project"""



### command line handler

class Email2Trac(Component) :

    
    implements(IAdminCommandProvider, IPermissionRequestor)


    def main(self, file) :
        # read the message
        f = open(file, 'r')
        message = f.read()
        try:
            self.mail2project(message)  # process the message
        except Exception, e:
            raise




    # IAdminCommandProvider methode
    def get_admin_commands(self) :
        yield ('email2Trac', '', 'use a mail saved in file to create or update ticket', None, self.main)



    # Ipermissionrequestor methode
    def get_permission_actions(self) :
        ticketPerm = ['MAIL2TICKET_COMMENT', 'MAIL2TICKET_PROPERTIES', 'MAIL2TICKET_CREATE']
        return ticketPerm + [('MAIL2TICKET_ADMIN', ticketPerm)]


    ### methods for email processing

    def lookup(self, message) :
        """
        matches a message with the environment and returns the message;
        on lookup error, raises AddressLookupException
        """
        message = email.message_from_string(message)
        
        # if the message is not to this project, ignore it
        trac_address = self.env.config.get('mail', 'address')
        if not trac_address:
            trac_address = self.env.config.get('notification', 'smtp_replyto')
        if not self.env.config.getbool('mail', 'accept_all') :
            to = list(email.Utils.parseaddr(message['to']))
            cc = message.get('cc','').strip()
            if cc:
                cc = [email.Utils.parseaddr(i.strip())[1] 
                      for i in cc.split(',') if i.strip()]
                to = to + cc
            delivered_to = message.get('delivered-to', '').strip()
            if delivered_to:
                to.append(email.Utils.parseaddr(delivered_to)[1])
            original_to = message.get('x-original-to', '').strip()
            if original_to:
                to.append(original_to)
    
            if trac_address not in to:
                raise AddressLookupException("Email (to : %s ) does not match Trac address: %s" %(str(to),  trac_address))
    
        return message
    
    def mail2project(self, message) :
        """relays an email message to a project"""
    
        # keep copy of original message for error handling
        original_message = email.message_from_string(message)
   
        #keep trac email : 
        trac_mail = self.env.config.get('notification', 'smtp_replyto')
 
        # whether or not to email back on error
        email_errors = self.env.config.getbool('mail', 'email_errors', True)
    
        # lookup the message
        message = self.lookup(message)
        # get the handlers
        handlers = ExtensionPoint(IEmailHandler).extensions(self.env)
        _handlers = self.env.config.getlist('mail', 'handlers')
        if not _handlers: # default value
            _handlers = [ 'RemoveQuotes', 'ReplyToTicket', 'EmailToTicket' ]
        handler_dict = dict([(h.__class__.__name__, h)
                                 for h in handlers])
        handlers = [handler_dict[h] for h in _handlers
                    if h in handler_dict ]
        # handle the message
        warnings = []
	#is this email treated ?
	email_treated = False
        for handler in handlers:
            if not handler.match(message) :
                continue
            try:
		email_treated = True

                message = handler.invoke(message, warnings)
            except Exception, e:
                # handle the error
                print "Exception in user code:"
                print '-'*60
                traceback.print_exc(file=sys.stdout)
                print '-'*60
                raise
            except EmailException, e:
                if email_errors and original_message['from']:
                    subject = reply_subject(original_message['subject'])
                    response = 'Subject: %s\n\n%s' % (subject, reply_body(str(e), original_message))
                    send_email(self.env,
                               trac_mail,
                               [ original_message['from'] ],
                               response
                               )
                    warnings = [] # clear warnings
                    return
                else:
                    raise
    
            # if the message is consumed, quit processing
            if not message:
                break
    
	if not email_treated :
	    warnings.append("Your email was not treated. It match none of the condition to be treated")
        # email warnings
        if warnings:
    
            # format warning message
            if len(warnings) == 1:
                body = warnings[0]
                pass
            else:
                body = "\n\n".join(["* %s" % warning.strip() 
                                    for warning in warnings])
            
            # notify the sender
            subject = reply_subject(original_message['subject'])
            response = 'Subject: %s\n\n%s' % (subject, reply_body(body, original_message))
            send_email(self.env,
                       trac_mail,
                       [ original_message['from'] ],
                       response
                       )
    
    
