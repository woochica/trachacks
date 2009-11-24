#!/usr/bin/env python

"""
email2trac:
a pluggable email handler plugin for Trac
http://trac.edgewall.org
"""

import email
import email.Utils
import os
import sys
import urllib
import urllib2

from datetime import datetime
from mail2trac.interface import IEmailHandler
from mail2trac.utils import reply_body
from mail2trac.utils import reply_subject
from mail2trac.utils import send_email
from trac.core import *
from trac.env import open_environment

# Meaningful exit-codes for a smtp-server
EXIT_USAGE = 64
EXIT_NOUSER = 67
EXIT_NOPERM = 77
EXIT_TEMPFAIL = 75

# exception classes
class EmailException(Exception):
    """error exception when processing email messages"""

class AddressLookupException(Exception):
    """exception when try to match the email address for a project"""

### methods for email processing

def lookup(env, message):
    """
    matches a message with the environment and returns the message;
    on lookup error, raises AddressLookupException
    """

    message = email.message_from_string(message)

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
            accept.update([email.Utils.parseaddr(delivered_to)[1]])
        original_to = message.get('x-original-to', '').strip()
        if original_to:
            accept.update([original_to])

        if trac_address not in accept:
            raise AddressLookupException("Email does not match Trac address: %s" % trac_address)

    return message

def mail2project(env, message):
    """relays an email message to a project"""

    # keep copy of original message for error handling
    original_message = email.message_from_string(message)

    # whether or not to email back on error
    email_errors = env.config.getbool('mail', 'email_errors', True)

    # lookup the message
    message = lookup(env, message)

    # get the handlers
    handlers = ExtensionPoint(IEmailHandler).extensions(env)
    _handlers = env.config.getlist('mail', 'handlers')
    if not _handlers: # default value
        _handlers = [ 'RemoveQuotes', 'ReplyToTicket', 'EmailToTicket' ]
    handler_dict = dict([(h.__class__.__name__, h)
                             for h in handlers])
    handlers = [handler_dict[h] for h in _handlers
                if h in handler_dict ]

    # handle the message
    warnings = []
    for handler in handlers:
        if not handler.match(message):
            continue
        try:
            message = handler.invoke(message, warnings)
        except EmailException, e:
            # handle the error
            if email_errors and original_message['from']:
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

### command line handler

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
    parser.add_option('-e', '--parent-env', dest='environment', 
                      help='Trac parent environment directory to dispatch TTW')
    parser.add_option('-l', '--logdir', dest='logdir',
                      help='directory to log emails that cause errors')
    options, args = parser.parse_args(args)

    # print help if no options given
    if not options.projects and not options.urls and not options.environment:
        parser.print_help()
        sys.exit()


    # read the message
    if options.file:
        f = file(options.file)
    else:
        f = sys.stdin
    message = f.read()

    try:

        # relay the email
        found = False

        for project in options.projects:
            found = True
            env = open_environment(project)  # open the environment
            mail2project(env, message)  # process the message
        
        if options.environment:
            assert len(options.urls) == 1
            base_url = options.urls[0].rstrip('/')
            projects = [ project for project in os.listdir(options.environment)
                         if os.path.isdir(os.path.join(options.environment, project)) ]
            options.urls = [ '%s/%s/mail2trac' % (base_url, project)
                             for project in projects ]

        for url in options.urls:
            # post the message
            try:
                urllib2.urlopen(url, urllib.urlencode(dict(message=unicode(message, 'utf-8', 'ignore'))))
            except urllib2.HTTPError, e:
                if options.environment:
                    continue
                else:
                    e.msg += '\n' + e.read()
                    raise e
            found = True

        # send proper status code if email is not relayed
        if not found:
            raise SystemExit(EXIT_NOUSER)

    except Exception, e:

        # logging
        if options.logdir:
            datestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            f = file(os.path.join(options.logdir, datestamp), 'w')
            print >> f, str(e)
            print >> f, '-' * 40 # separator
            print >> f, message
            f.close()

        raise
            
if __name__ == '__main__':
    main()
