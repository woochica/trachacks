#!/usr/bin/env python

"""
email2trac:
a pluggable email handler plugin for Trac
http://trac.edgewall.org
"""

import email
import email.Utils
import sys
import urllib
import urllib2

from mail2trac.interface import IEmailHandler
from mail2trac.utils import reply_body
from mail2trac.utils import reply_subject
from mail2trac.utils import send_email
from trac.core import *
from trac.env import open_environment

class EmailException(Exception):
    """error exception when processing email messages"""

def mail2project(env, message):
    """relays an email message to a project"""

    # read the email
    original_message = email.message_from_string(message)
    message = email.message_from_string(message)

    # whether or not to email back on error
    email_errors = env.config.getbool('mail', 'email_errors', True)

    # if the message is not to this project, ignore it
    trac_address = env.config.get('mail', 'address')
    if not trac_address:
        trac_address = env.config.get('notification', 'smtp_replyto')
    if not env.config.getbool('mail', 'accept_all'):
        to = email.Utils.parseaddr(message['to'])[1]
        accept = set([to])
        cc = message.get('cc','').strip()
        if cc:
            cc = [email.Utils.parseaddr(i.strip())[1] 
                  for i in cc.split(',') if i.strip()]
            accept.update(cc)
        delivered_to = message.get('delivered-to', '').strip()
        if delivered_to:
            accept = set([email.Utils.parseaddr(delivered_to)[1]])
    
        if trac_address not in accept:
            raise EmailException("Email does not match Trac address: %s" % trac_address)

    
    # handle the message
    handlers = ExtensionPoint(IEmailHandler).extensions(env)
    handlers.sort(key=lambda x: x.order(), reverse=True)
    warnings = []
    for handler in handlers:
        try:
            message = handler.invoke(message, warnings)
        except EmailException, e:
            # handle the error
            if email_errors:
                subject = reply_subject(original_message['subject'])
                response = 'Subject: %s\n\n%s' % (subject, reply_body(str(e), original_message))
                send_email(env, 
                           original_message['to'],
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
        send_email(env, 
                   original_message['to'],
                   [ original_message['from'] ],
                   response
                   )

def main(args=sys.argv[1:]):

    # parse the options
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-p', '--project', '--projects', 
                      dest='projects', action='append', 
                      default=[], 
                      help='projects to apply to',)
    parser.add_option('-f', '--file', dest='file',
                      help='email file to read;  if not specified, taken from stdin')
    parser.add_option('-u', '--url', '--urls', 
                      dest='urls', action='append', default=[],
                      help='urls to post to')
    options, args = parser.parse_args(args)

    # print help if no options given
    if not options.projects and not options.urls:
        parser.print_help()
        sys.exit()

    # read the message
    if options.file:
        f = file(options.file)
    else:
        f = sys.stdin
    message = f.read()

    # relay the email
    for project in options.projects:
        env = open_environment(project)  # open the environment
        mail2project(env, message)  # process the message
        
    for url in options.urls:
        # post the message
        try:
            urllib2.urlopen(url, urllib.urlencode(dict(message=message)))
        except urllib2.HTTPError, e:
            print e.read()
            sys.exit(1)

if __name__ == '__main__':
    main()
