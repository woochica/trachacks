# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8 et
# ==============================================================================
# Copyright © 2008 UfSoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# ==============================================================================

__version__     = '0.2.2'
__author__      = 'Pedro Algarvio'
__email__       = 'ufs@ufsoft.org'
__package__     = 'TracGoogleAnalytics'
__license__     = 'BSD'
__url__         = 'http://google.ufsoft.org'
__summary__     = 'Trac plugin to enable your trac environment to be logged' + \
                  ' by Google Analytics'

import pkg_resources
from trac.config import Option, BoolOption
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import ITemplateProvider

# ==============================================================================
# Google Analytics Configuration
# ==============================================================================
class GoogleAnalyticsConfig(Component):
    uid = Option(
        'google.analytics', 'uid', None,
        """Google Analytics' UID.
        The UID is needed for Google Analytics to log your website stats.
        Your UID can be found by looking in the JavaScript Google Analytics
        gives you to put on your page. Look for your UID in between
        `var pageTracker = _gat._getTracker("UA-111111-11");` in the javascript.
        In this example you would put UA-11111-1 in the UID box.""")
    admin_logging = BoolOption(
        'google.analytics', 'admin_logging', False,
        """Disabling this option will prevent all logged in admins from showing
        up on your Google Analytics reports.""")
    authenticated_logging = BoolOption(
        'google.analytics', 'authenticated_logging', True,
        """Disabling this option will prevent all authenticated users from
        showing up on your Google Analytics reports.""")
    outbound_link_tracking = BoolOption(
        'google.analytics', 'outbound_link_tracking', True,
        """Disabling this option will turn off the tracking of outbound links.
        It's recommended not to disable this option unless you're a privacy
        advocate (now why would you be using Google Analytics in the first
        place?) or it's causing some kind of weird issue.""")
    google_external_path = Option(
        'google.analytics', 'google_external_path', '/external/',
        """This will be the path shown on Google Analytics
        regarding external links. Consider the following link:
          http://trac.edgewall.org/"
        The above link will be shown as for example:
          /external/trac.edgewall.org/
        This way you will be able to track outgoing links.
        Outbound link tracking must be enabled for external links to be
        tracked.""")
    extensions = Option(
        'google.analytics', 'extensions', 'zip,tar,tar.gz,tar.bzip,egg',
        """Enter any extensions of files you would like to be tracked as a
        download. For example to track all MP3s and PDFs enter:
            mp3,pdf
        Outbound link tracking must be enabled for downloads to be tracked.""")
    tracking_domain_name = Option(
        'google.analytics', 'tracking_domain_name', None,
        """If you're tracking multiple subdomains with the same Google Analytics
        profile, like what's talked about in:
            https://www.google.com/support/googleanalytics/bin/answer.py?answer=55524
        enter your main domain here. For more info, please visit the previous
        link.""")

# ==============================================================================
# Google Analytics Resources
# ==============================================================================
class GoogleAnalyticsResources(Component):
    implements(ITemplateProvider)
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        yield 'googleanalytics', pkg_resources.resource_filename(__name__,
                                                                 'htdocs')

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        yield pkg_resources.resource_filename(__name__, 'templates')

# ==============================================================================
# Upgrade Code
# ==============================================================================
class GoogleAnalyticsSetup(Component):
    env = config = log = None # make pylink happy
    implements(IEnvironmentSetupParticipant)

    def environment_created(self):
        "Nothing to do when an environment is created"""

    def environment_needs_upgrade(self, db):
        return 'google_analytics' in self.config

    def upgrade_environment(self, db):
        # Although we're only migrating configuration stuff and there's no
        # database queries involved, which could be done on other places,
        # I'm placing the migration code here so that it only happens once
        # and the admin notices that a migration was done.
        self.log.debug('Migrating Google Analytics configuration')
        for option, value in self.config.options('google_analytics'):
            if self.config.has_option('google.analytics', option):
                self.config.set('google.analytics', option, value)
            self.config.remove('google_analytics', option)
        self.config.save()
