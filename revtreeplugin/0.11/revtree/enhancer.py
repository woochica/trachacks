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

from revtree import IRevtreeEnhancer
from revtree.svgview import SvgOperation, SvgGroup
from trac.core import *


class SimpleContainer(object):
    """Simple container for enhancer parameters"""
    
    def __init__(self):
        pass
        

class SimpleEnhancer(Component):
    """Enhance the appearance of the RevTree with site-specific properties.
    
    Create branch clone operation (on branch/tag operations)
    
    This class is a very basic skeleton that needs to customized, to provide
    SvgOperation, SvgGroup and other widgets in the RevTree graphic
    """
    
    implements(IRevtreeEnhancer)    
    
    def create(self, env, req, repos, svgrevtree):
        """Creates the internal data from the repository"""
        enhancer = SimpleContainer()
        enhancer.repos = repos
        enhancer.creations = []
        enhancer.deliveries = []
        enhancer.groups = []
        enhancer.svgrevtree = svgrevtree
        # z-depth indexed widgets: back=1, fore=2
        enhancer.widgets = ([], [], [])
        
        #self._sort()
        for branch in enhancer.repos.branches().values():
            svgbranch = enhancer.svgrevtree.svgbranch(branch=branch)
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
                srcchg = enhancer.repos.changeset(rev)
                if srcchg is None:
                    continue
                # .. and create an operation between both changesets
                enhancer.creations.append((srcchg, firstchgset))
            lastchgset = branch.youngest()
            if lastchgset:
                # if the last changeset of the branch is the very last
                if lastchgset.last:
                    # tweak the color of this changeset
                    svgbranch.svgchangeset(lastchgset).mark_last()
        return enhancer

    def build(self, enhancer):
        """Build the enhanced widgets"""
        for (srcchg, dstchg) in enhancer.creations:
            svgsrcbr = enhancer.svgrevtree.svgbranch(branchname=srcchg.branchname)
            if svgsrcbr is None:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstbr = enhancer.svgrevtree.svgbranch(branchname=dstchg.branchname)
            if svgdstbr is None:
                continue
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(enhancer.svgrevtree, svgsrcchg, svgdstchg, \
                              '#5faf5f')
            enhancer.widgets[2].append(op)
                    
        for wl in enhancer.widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, enhancer, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(enhancer.widgets):
            map(lambda w: w.render(), enhancer.widgets[level])
            


        