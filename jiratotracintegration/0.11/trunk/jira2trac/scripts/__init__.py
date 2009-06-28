# Copyright (c) 2008-2009 The Jira2Trac Project.
# See LICENSE.txt for details.

"""
The jira2trac daemon.

@since: 2009-06-25
"""


import logging as log

from time import time
from decimal import Decimal
from optparse import OptionParser

from jira2trac import version
from jira2trac import JiraDecoder
from jira2trac import TracEncoder


def run():
    name = "Jira2Trac"
    usage = "Usage: %s [options]" % name
    
    parser = OptionParser(usage=usage, version="%s %s" % (name, version))
    parser.add_option("-i", "--input", dest="input",
                      help="Location of Jira backup XML file", metavar="FILE")
    parser.add_option("-a", "--attachments", dest="attachments", metavar="FILE",
                      help="Location of the Jira attachments folder")
    parser.add_option("-t", "--authentication", dest="authentication", metavar="FILE",
                      help="Location of the .htpasswd file (optional)")
    parser.add_option("-l", "--url", dest="url", help="URL for Trac instance")
    parser.add_option("-u", "--username", dest="username", help="Username for Trac instance")
    parser.add_option("-p", "--password", dest="password", help="Password for Trac instance")
    parser.add_option("-v", "--verbose", default=False, action="store_true",
                      help="Print debug messages to stdout [default: %default]",
                      dest="verbose")

    (options, args) = parser.parse_args()

    FORMAT = "%(message)s"
    LEVEL = log.INFO

    if options.verbose == True:
        FORMAT = "%(asctime)-15s - %(levelname)-3s - " + FORMAT
        LEVEL = log.DEBUG

    log.basicConfig(format=FORMAT, level=LEVEL)

    if options.input:
        start = time()
        jira = JiraDecoder(options.input)

        try:
            jira.parseBackupFile()
            jira.showResults()            
        except KeyboardInterrupt:
            log.warn('Cancelled data parsing!')
            exit()

        if options.username:
            trac = TracEncoder(jira.data, options.username, options.password,
                               options.url, options.attachments,
                               options.authentication)
            try:
                trac.importData()

                if options.authentication is not None:
                    trac.importUsers()

            except KeyboardInterrupt:
                log.warn('Cancelled data import!')
                exit()

        end = time() - start

        log.info('Completed in %s sec.' % (Decimal(str(end)).quantize(Decimal('.0001'))))

    else:
        parser.error("Please specify a value for the 'input' option")


__all__ = ['run']