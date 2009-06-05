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
from trac.core import *
from trac.env import open_environment


class EmailException(Exception):
    """exception when processing email messages"""

def mail2project(env, message):
    """relays an email message to a project"""

    # read the email
    message = email.message_from_string(message)

    # if the message is not to this project, ignore it
    trac_address = env.config.get('mail', 'address')
    if not trac_address:
        trac_address = env.config.get('notification', 'smtp_replyto')
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
        # XXX should be made more robust
        raise EmailException("Email does not match Trac address: %s" % trac_address)

    # handle the message
    handlers = ExtensionPoint(IEmailHandler).extensions(env)

    handlers.sort(key=lambda x: x.order(), reverse=True)
    for handler in handlers:
        try:
            message = handler.invoke(message)
        except EmailException:
            # TODO : handle the exception
            raise

        # if the message is consumed, quit processing
        if not message:
            break
    

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
        urllib2.urlopen(url, urllib.urlencode(dict(message=message)))

if __name__ == '__main__':
    main()
