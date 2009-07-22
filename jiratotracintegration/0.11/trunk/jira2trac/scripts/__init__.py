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
from jira2trac import util


def run():
    name = "jira2trac"
    usage = "Usage: {} [options]".format(name)

    parser = OptionParser(usage=usage, version="{} {}".format(name, version))
    parser.add_option("-n", "--new", default=False, action="store_true",
                      help="Create a temporary Trac instance [default: %default]",
                      dest="new")
    parser.add_option("-c", "--config", dest="config", metavar="FILE",
                      default="settings.cfg",
                      help="Location of configuration file [default: %default]")
    parser.add_option("-i", "--input", dest="input",
                      help="Location of Jira backup XML file", metavar="FILE")
    parser.add_option("-a", "--attachments", dest="attachments", metavar="FOLDER",
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
    cfg = util.load_config(options.config)

    try:
        if len(cfg.sections()) == 0:
            raise AttributeError

        options.verbose = cfg.getboolean('general', 'verbose')
        options.username = cfg.get('trac', 'username')
        options.password = cfg.get('trac', 'password')
        options.url = cfg.get('trac', 'url')
        options.authentication = cfg.get('trac', 'authentication')
        options.attachments = cfg.get('jira', 'attachments')
        options.input = cfg.get('jira', 'backup')

    except AttributeError:
        if options.input is None:
            parser.error("Please specify a valid 'input' or 'config' option")

    startup(options)


def startup(opt):
    util.setup_logging(opt.verbose)
    start = time()

    # optionally create a new local Trac instance
    if opt.new:
        tmp_trac = util.TemporaryTrac(opt.url)
        trac_path = tmp_trac.create()
         # give user admin permissions
        make_admin = tmp_trac.add_permission(opt.username, 'TRAC_ADMIN')
        update_config = tmp_trac.setup()

    # start the import process
    jira = JiraDecoder(opt.input)

    try:
        jira.parse_backup_file()
        jira.show_results()
    except KeyboardInterrupt:
        log.warn("Cancelled data parsing!")
        exit()

    if opt.username:
        trac = TracEncoder(jira.data, opt.username, opt.password, opt.url,
                           opt.attachments, opt.authentication)
        try:
            trac.import_data()

            if opt.authentication is not None:
                trac.import_users()

        except KeyboardInterrupt:
            log.warn("Cancelled data import!")
            exit()

    end = time() - start

    log.info("Completed in {} sec.".format(Decimal(str(end)).quantize(Decimal('.0001'))))


__all__ = ['run']
