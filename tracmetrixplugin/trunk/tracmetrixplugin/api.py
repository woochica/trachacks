# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Bhuricha Sethanadha <khundeen@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac-hacks.org/wiki/TracMetrixPlugin.
#
# Author: Bhuricha Sethanandha <khundeen@gmail.com>

import os
from trac.core import Component, implements
from trac.env import IEnvironmentSetupParticipant


class TracMetrixSetupParticipant(Component):
    """
        This class make sure that the enviroment has what TracMetrix Needs.
        
        1) The cache folder for chart
        2) Database
        3) Required plugins
    
    """
    implements(IEnvironmentSetupParticipant)
    
    
    def environment_created(self):
        """Called when a new Trac environment is created."""
        if self.environment_needs_upgrade(None):
            self.upgrade_environment(None)
            
            
    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        return (self._cachefolder_needs_upgrade())

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """
        
        if self._cachefolder_needs_upgrade():
            path = os.path.join(self.env.path, 'cache', 'tracmetrixplugin')
            try:
                os.makedirs(path)
            except OSError, e:
                print "Upgrade failed: Could not create path %s" % path
                print e
        
    def _cachefolder_needs_upgrade(self):
        # Check if the cache exist
        path = os.path.join(self.env.path, 'cache', 'tracmetrixplugin')
        return not os.path.exists(path)
        
