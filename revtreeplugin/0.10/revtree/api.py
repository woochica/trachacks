# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#

from trac.config import ExtensionOption
from trac.core import *


class IRevtreeEnhancer(Interface):
    """Provide graphical enhancements to a revision tree"""

    def create(env, req, repos, svgrevtree):
        """Create the internal data from the repository"""
        
    def build(enhancer):
        """Build the widgets"""

    def render(enhancer, level):
        """Render the widgets"""


class IRevtreeOptimizer(Interface):
    """Provide optimized location for revision tree elements"""
    
    def optimize_branches(repos, branches):
        """Sort the branch elements.
        
        Return an placement ordered list, from the left-most to the right-most
        branch. 
        """


class EmptyRangeError(TracError):
    """Defines a RevTree error (no changeset in the selected range)"""
    def __init__(self, msg=None):
        TracError.__init__(self, "%sNo changeset" \
                           % (msg and '%s: ' % msg or ''))
                           

class RevtreeSystem(Component):
    """ """
    
    enhancers = ExtensionPoint(IRevtreeEnhancer)
    optimizer = ExtensionOption('revtree', 'optimizer', IRevtreeOptimizer,
                                'DefaultRevtreeOptimizer',
        """Name of the component implementing `IRevtreeOptimizer`, which is 
        used for optimizing revtree element placements.""")
    
    def get_revtree(self, repos):
        self.urlbase = self.config.get('trac', 'base_url')
        if not self.urlbase:
            raise TracError, "Base URL not defined"
        self.env.log.debug("Enhancers: %s" % self.enhancers)
        from revtree.svgview import SvgRevtree
        return SvgRevtree(self.env, repos, self.urlbase, 
                          self.enhancers, self.optimizer)
