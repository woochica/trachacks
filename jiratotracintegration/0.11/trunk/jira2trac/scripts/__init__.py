# Copyright (c) 2008-2009 The Jira2Trac Project.
# See LICENSE.txt for details.

"""
The jira2trac daemon.

@since: 2009-06-25
"""

import os.path
import configparser
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
    parser.add_option("-c", "--config", dest="config",
                      help="Location of configuration file", metavar="FILE")
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
    cfg = load_config(options.config)

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

    execute(options)


def setup_logging(verbose):
    FORMAT = "%(message)s"
    LEVEL = log.INFO

    if verbose == True:
        FORMAT = "%(asctime)-15s - %(levelname)-3s - " + FORMAT
        LEVEL = log.DEBUG

    log.basicConfig(format=FORMAT, level=LEVEL)


def load_config(cfg):
    if cfg and os.path.exists(cfg) is False:
        return None

    config = configparser.RawConfigParser()
    try:
        config.read(cfg)
    except TypeError:
        return None

    return config


def execute(opt):
    setup_logging(opt.verbose)
    start = time()
    jira = JiraDecoder(opt.input)

    try:
        jira.parseBackupFile()
        jira.showResults()
    except KeyboardInterrupt:
        log.warn('Cancelled data parsing!')
        exit()

    if opt.username:
        trac = TracEncoder(jira.data, opt.username, opt.password, opt.url,
                           opt.attachments, opt.authentication)
        try:
            trac.importData()

            if opt.authentication is not None:
                trac.importUsers()

        except KeyboardInterrupt:
            log.warn('Cancelled data import!')
            exit()

    end = time() - start

    log.info('Completed in %s sec.' % (Decimal(str(end)).quantize(Decimal('.0001'))))


__all__ = ['run']
