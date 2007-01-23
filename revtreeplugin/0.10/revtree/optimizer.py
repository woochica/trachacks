# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2007 Emmanuel Blot <emmanuel.blot@free.fr>
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

from revtree.api import IRevtreeOptimizer
from trac.core import *

__all__ = ['DefaultRevtreeOptimizer']

class DefaultRevtreeOptimizer(Component):
    """Default optmizer"""
    
    implements(IRevtreeOptimizer)    
        
    def optimize(self, repos, branches):
        """Computes the optimal placement of branches.
        
        Optimal placement is recommended to reduce the number of operation 
        links that cross each other on the rendered graphic.
        This rudimentary example is FAR from providing optimal placements...
        """
        # FIXME: really stupid algorithm
        graph = {}
        for v in repos.branches().values():
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
        nbranches = []
        for br in graph.values():
            nbranches.extend(br)
        nbranches.extend([br.name for br in repos.branches().values() \
                          if br.name not in nbranches])
        for branch in nbranches:
            if branch in order:
                continue
            order.insert(cur, branch)
            if cur:
                cur = 0
            else:
                cur = len(order)
        obranches = [repos.branch(name) for name in order]
        # FIXME: use filter()
        return [b for b in obranches if b in branches]
