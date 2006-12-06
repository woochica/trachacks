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

from revtree.svgview import SvgOperation, SvgGroup


class Enhancer(object):
    """Enhance the appearance of the RevTree with site-specific properties
    This file is a very basic skeleton that needs to customized, to provide
    SvgOperation, SvgGroup and other widgets in the RevTree graphic"""
    
    def __init__(self, repos, svgrevtree):
        self._repos = repos
        self._creations = []
        self._deliveries = []
        self._groups = []
        self._svgrevtree = svgrevtree
        # z-depth indexed widgets: back=1, fore=2
        self._widgets = ([], [], [])

    def create(self):
        """Creates the internal data from the repository"""
        self._sort()
        for branch in self._repos.branches().values():
            svgbranch = self._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                # branch has probably been filtered out
                continue
            firstchgset = branch.oldest()
            # if the first changeset of a branch is a copy of another
            # changeset(from another branch)
            if firstchgset and firstchgset.clone:
                # tweak the color appearance of this changeset ..
                svgbranch.svgchangeset(firstchgset).invert_color()
                (rev, path) = branch.source()
                srcchg = self._repos.changeset(rev)
                if srcchg is None:
                    continue
                # .. and create an operation between both changesets
                self._creations.append((srcchg, firstchgset))
            lastchgset = branch.youngest()
            if lastchgset:
                # if the last changeset of the branch is the very last
                if lastchgset.last:
                    # tweak the color of this changeset
                    svgbranch.svgchangeset(lastchgset).kill()

    def build(self):
        """Build the enhanced widgets"""
        for (srcchg, dstchg) in self._creations:
            svgsrcbr = self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            if svgsrcbr is None:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstbr = self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if svgdstbr is None:
                continue
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, '#5faf5f')
            self._widgets[2].append(op)
                    
        for wl in self._widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, level):
        """Renders widgets, from background plane to foreground plane"""
        if level < len(self._widgets):
            map(lambda w: w.render(), self._widgets[level])
        
    def optimize(self, branches):
        """Provides a list of branches, sorted from left-most to rigtht-most
        position.
        Optimal placement is required to reduce the number of operation links
        that cross each other on the rendered graphic"""
        return [b for b in self._obranches if b in branches]
        
    def _sort(self):
        """Computes the optimal placement of branches.
        This example is FAR from providing optimal placements ;-)"""
        graph = {}
        for v in self._repos.branches().values():
            k = v.name
            src = v.source()
            if src:
                (rev, path) = src
                if graph.has_key(path):
                    graph[path].append(k)
                else:
                    graph[path] = [k]
        density = []
        for (p, v) in graph.items():
            density.append((p,len(v)))
        density.sort(lambda a,b: cmp(a[1],b[1]))
        density.reverse()
        order = []
        cur = 0
        for (branch, weight) in density:
            order.insert(cur, branch)
            if cur:
                cur = 0
            else:
                cur = len(order)
        branches = []
        for br in graph.values():
            branches.extend(br)
        branches.extend([br.name for br in self._repos.branches().values() \
                         if br.name not in branches])
        for branch in branches:
            if branch in order:
                continue
            order.insert(cur, branch)
            if cur:
                cur = 0
            else:
                cur = len(order)
        self._obranches = [self._repos.branch(name) for name in order]
 
