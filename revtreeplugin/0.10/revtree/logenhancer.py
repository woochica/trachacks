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
    """Improved enhancer, based on specific log messages and custom properties
    This class is provided as-is, as an example"""
    
    def __init__(self, repos, svgrevtree):
        self._repos = repos
        self._creations = []
        self._deliveries = []
        self._groups = []
        self._svgrevtree = svgrevtree
        # z-depth indexed widgets: back=1, fore=2
        self._widgets = ([], [], [])
        
    def create(self):
        self._sort()
        for branch in self._repos.branches().values():
            svgbranch = self._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            firstchgset = branch.oldest()
            if firstchgset:
                msg = firstchgset.changeset.message.lower()
                if msg.startswith('creates'):
                    svgbranch.svgchangeset(firstchgset).invert_color()
                    if branch.source():
                        (rev, path) = branch.source()
                        srcchg = self._repos.changeset(rev)
                        if srcchg is None:
                            continue
                        self._creations.append((srcchg, firstchgset))
            lastchgset = branch.youngest()
            if lastchgset:
                msg = lastchgset.changeset.message.lower()
                if msg.startswith('terminates'):
                    svgbranch.svgchangeset(lastchgset).kill()

        for branch in self._repos.branches().values():
            svgbranch = self._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            for chgset in branch.changesets():
                msg = chgset.changeset.message.lower()
                if msg.startswith('delivers'):
                    if chgset.prop('st:export'):
                        svgchgset = svgbranch.svgchangeset(chgset)
                        svgchgset.set_shape('hexa')
                    deliver = chgset.prop('st:deliver')
                    if not deliver:
                        continue
                    try:
                        revisions = [int(c) for c in deliver.split(',')]
                        revisions.sort()
                        ychg = self._repos.changeset(revisions[-1])
                        if not ychg:
                            continue
                        brname = ychg.branchname
                        srcbranch = self._repos.branch(brname)
                        if not srcbranch:
                            continue
                        brrevs = [c.rev for c in srcbranch.changesets()]
                        valrevs = [r for r in revisions if r in brrevs]
                        fchg = self._repos.changeset(valrevs[0])
                        lchg = self._repos.changeset(valrevs[-1])
                        self._groups.append((fchg,lchg))
                        self._deliveries.append((lchg,chgset))
                    except ValueError:
                        pass
                    except IndexError:
                        pass
                    #if stprops:
                    #    print "%s:%s: %s" % (branch.name, changeset.revision, stprops)
                    #else:
                    #    print "%s:%s: %s" % (branch.name, changeset.revision, changeset.log)
                elif msg.startswith('imports'):
                    svgchgset = svgbranch.svgchangeset(chgset)
                    svgchgset.set_shape('Circle')
                
    def build(self):
        for (srcchg, dstchg) in self._creations:
            svgsrcbr = self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, '#5faf5f')
            self._widgets[2].append(op)
        
        for (first, last) in self._groups:
            svgbranch = self._svgrevtree.svgbranch(branchname=first.branchname)
            if not svgbranch:
                continue
            fsvg = svgbranch.svgchangeset(first)
            lsvg = svgbranch.svgchangeset(last)
            group = SvgGroup(self._svgrevtree, fsvg, lsvg)
            self._widgets[1].append(group)
        
        for (srcchg, dstchg) in self._deliveries:
            svgsrcbr = self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, 'blue')
            self._widgets[2].append(op)
            
        for wl in self._widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, level):
        if level < len(self._widgets):
            map(lambda w: w.render(), self._widgets[level])
        
    def optimize(self, branches):
        return [b for b in self._obranches if b in branches]
        
    def _sort(self):
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
