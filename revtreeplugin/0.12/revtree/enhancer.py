# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Emmanuel Blot <emmanuel.blot@free.fr>
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

from revtree.api import IRevtreeEnhancer, RevtreeEnhancer
from revtree.svgview import SvgOperation, SvgGroup
from trac.core import *

__all__ = ['SimpleEnhancerModule']


class SimpleEnhancer(RevtreeEnhancer):
    """This class is a very basic skeleton that needs to customized, to 
       provide SvgOperation, SvgGroup and other widgets in the RevTree graphic
    """
        
    def __init__(self, env, req, repos, svgrevtree):
        """Creates the internal data from the repository"""
        self.repos = repos
        self.creations = []
        self.svgrevtree = svgrevtree
        # z-depth indexed widgets
        self._widgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        
        for branch in self.repos.branches().values():
            svgbranch = self.svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                # branch has probably been filtered out
                continue
            firstchgset = branch.oldest()
            # if the first changeset of a branch is a copy of another
            # changeset(from another branch)
            if firstchgset and firstchgset.clone:
                # tweak the appearance of this changeset ..
                svgbranch.svgchangeset(firstchgset).mark_first()
                (rev, path) = branch.source()
                srcchg = self.repos.changeset(rev)
                if srcchg is None:
                    continue
                # .. and create an operation between both changesets
                self.creations.append((srcchg, firstchgset))
            lastchgset = branch.youngest()
            if lastchgset:
                # if the last changeset of the branch is the very last
                if lastchgset.last:
                    # tweak the color of this changeset
                    svgbranch.svgchangeset(lastchgset).mark_last()

    def build(self):
        """Build the enhanced widgets"""
        for (srcchg, dstchg) in self.creations:
            svgsrcbr = self.svgrevtree.svgbranch(branchname=srcchg.branchname)
            if svgsrcbr is None:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstbr = self.svgrevtree.svgbranch(branchname=dstchg.branchname)
            if svgdstbr is None:
                continue
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self.svgrevtree, svgsrcchg, svgdstchg, '#3f3f3f')
            self._widgets[IRevtreeEnhancer.ZFORE].append(op)
                    
        for wl in self._widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(IRevtreeEnhancer.ZLEVELS):
            map(lambda w: w.render(), self._widgets[level])


class SimpleEnhancerModule(Component):
    """Enhance the appearance of the RevTree with site-specific properties.
    
    Create branch clone operation (on branch/tag operations)
    
    This class is a very basic skeleton that needs to customized, to provide
    SvgOperation, SvgGroup and other widgets in the RevTree graphic
    """
    
    implements(IRevtreeEnhancer)    

    def create(self, env, req, repos, svgrevtree):
        return SimpleEnhancer(env, req, repos, svgrevtree)
