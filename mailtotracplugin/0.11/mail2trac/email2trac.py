#!/usr/bin/env python

"""
email2trac:
a email handler plugin for Trac
http://trac.edgewall.org
"""

import email
import email.Utils

import sys

from mail2trac.interface import IEmailHandler

from trac.core import *
from trac.env import open_environment


class EmailException(Exception):
    """exception when processing email messages"""

def mail2project(project, message):
    """
    relays an email message to a project
    
    """

    # open the environment
    env = open_environment(project)

    # read the email
    message = email.message_from_string(message)

    # if the message is not to this project, ignore it
    to = email.Utils.parseaddr(message['to'])[1]
    if to != env.config.get('notification', 'smtp_replyto'):
        # XXX should be made more robust
        return

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
                      help='projects to apply to',
                      )
    parser.add_option('-f', '--file',
                      dest='file',
                      help='email file to read;  if not specified, taken from stdin')

    options, args = parser.parse_args(args)

    if options.file:
        f = file(options.file)
    else:
        f = sys.stdin

    if not options.projects:
        parser.print_help()
        sys.exit()

    # relay the email
    for project in options.projects:
        mail2project(project, f.read())
        
if __name__ == '__main__':
    main()
