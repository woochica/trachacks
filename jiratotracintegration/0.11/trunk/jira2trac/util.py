# Copyright (c) 2008-2009 The Jira2Trac Project.
# See LICENSE.txt for details.


"""
Utilities.
"""

import os
import sys
import subprocess
import logging as log

from hashlib import sha512
from base64 import b64encode
from tempfile import mkdtemp
from urllib.parse import urlparse
from configparser import RawConfigParser


class TemporaryTrac(object):
    """
    A temporary Trac environment.
    
    @since: 0.2
    """

    def __init__(self, url, project_name='Jira to Trac - Imported',
                 db='sqlite:db/trac.db', scm_path='/path/to/repos',
                 scm_type='svn', admin_cmd='trac-admin'):
        """
        @param url: URL where this Trac instance should run.
        """
        self.url = url
        self.project_name = project_name
        self.db = db
        self.scm_path = scm_path
        self.scm_type = scm_type
        self.admin_cmd = admin_cmd

    def create(self):
        """
        Creates a new Trac instance.
        """

        # find Trac version number
        v = self.admin('--version')

        try:
            self.version = v[0].split(' ')[1]
        except (IndexError, BaseException):
            log.error('Could not find {}, aborting!'.format(v))
            exit()

        # create temporary environment folder for trac
        tmp_dir = mkdtemp()
        self.path = urlparse(self.url).path
        
        if self.path:
            self.path = os.path.join(tmp_dir,
                    self.path.lstrip('/').rstrip('/'))

        log.info('Creating temporary Trac {} instance...'.format(self.version))
        os.mkdir(self.path)

        # setup a new trac
        cmd = "{} initenv '{}' {} {} {}".format(self.path, self.project_name,
            self.db, self.scm_type, self.scm_path)
        new_trac = self.admin(cmd)

        return self.path

    def add_permission(self, user, perm):
        cmd = "{} permission add {} {}".format(self.path, user, perm)
        log.info("Adding {} permission for user '{}'...".format(perm, user))

        return self.admin(cmd)       

    def admin(self, cmd):
        cmd = '{} {}'.format(self.admin_cmd, cmd)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE)

        return str(proc.communicate()[0], encoding='utf-8').rsplit('\n')

    def setup(self):
        self.config_path = os.path.join(self.path, 'conf', 'trac.ini')
        self.config = load_config(self.config_path)
        log.info("Updating trac.ini...")
        
        return self.config


def setup_logging(verbose):
    f = "%(asctime)-15s - %(message)s"
    l = log.INFO

    if verbose == True:
        f = "%(levelname)-3s - " + f
        l = log.DEBUG

    log.basicConfig(format=f, level=l)


def load_config(cfg_path):
    if cfg_path and os.path.exists(cfg_path) is False:
        return None

    config = RawConfigParser()
    try:
        config.read(cfg_path)
    except TypeError:
        return None

    return config


def create_hash(password):
    """
    Turns strings into base64 encoded SHA-512 hashes.
    
    For example, the word 'sphere' should produce the hash:
    uQieO/1CGMUIXXftw3ynrsaYLShI+GTcPS4LdUGWbIusFvHPfUzD7CZvms6yMMvA8I7FViHVEqr6Mj4pCLKAFQ==
    
    @param password: Password to turn into a hash
    @type password: C{str}
    """

    digested = sha512(bytes(password, 'utf-8')).digest()
    hash = b64encode(digested)

    return str(hash, encoding='utf8')


class ProgressBar:
    """
    Creates a text-based progress bar. Call the object with the `print'
    command to see the progress bar, which looks something like this::

        [=======>        22%                  ]

    You may specify the progress bar's width, min and max values on init.
    
    @note: Taken from U{http://code.activestate.com/recipes/168639}
    """

    def __init__(self, minValue = 0, maxValue = 100, totalWidth=40):
        self.progBar = "[]"   # This holds the progress bar string
        self.min = minValue
        self.max = maxValue
        self.span = maxValue - minValue
        self.width = totalWidth
        self.amount = 0       # When amount == max, we are 100% done
        self.updateAmount(0)  # Build progress bar string

    def updateAmount(self, newAmount = 0):
        """
        Update the progress bar with the new amount (with min and max
        values set at initialization; if it is over or under, it takes the
        min or max value as a default.
        """
        if newAmount < self.min: newAmount = self.min
        if newAmount > self.max: newAmount = self.max
        self.amount = newAmount

        # Figure out the new percent done, round to an integer
        diffFromMin = float(self.amount - self.min)
        percentDone = (diffFromMin / float(self.span)) * 100.0
        percentDone = int(round(percentDone))

        # Figure out how many hash bars the percentage should be
        allFull = self.width - 2
        numHashes = (percentDone / 100.0) * allFull
        numHashes = int(round(numHashes))

        # Build a progress bar with an arrow of equal signs; special cases for
        # empty and full
        if numHashes == 0:
            self.progBar = "[>{}]".format(' ' * (allFull - 1))
        elif numHashes == allFull:
            self.progBar = "[{}]".format('=' * allFull)
        else:
            self.progBar = "[{}>{}]".format('=' * (numHashes - 1),
                                        ' ' * (allFull - numHashes))

        # figure out where to put the percentage, roughly centered
        percentPlace = int(len(self.progBar) / 2) - len(str(percentDone))
        percentString = str(percentDone) + "%"
        
        # slice the percentage into the bar
        self.progBar = ' '.join([self.progBar[0:percentPlace], percentString,
                                self.progBar[percentPlace + len(percentString):]
                                ])

    def __str__(self):
        return str(self.progBar)


class DisplayProgress(object):
    """
    Display progress bar.
    """

    def __init__(self, total, title):
        self.progress = 0
        self.title = title
        self.total = total
        self.pb = ProgressBar(self.progress, self.total)
        log.info('  {} {}...'.format(self.total, self.title))

    def update(self):
        self.progress += 1
        self.pb.updateAmount(self.progress)
        sys.stdout.write("{}{}".format(str(self.pb), '\r'))
        sys.stdout.flush()
