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

from revtree import IRevtreeEnhancer, RevtreeEnhancer
from revtree.svgview import SvgOperation, SvgGroup
from trac.core import *

__all__ = ['LogEnhancerModule']


class LogEnhancer(RevtreeEnhancer):
    """Revtree enhancer based on specific log messages and custom properties
    This class is provided as-is, as an example

    'rth' stands for 'RevTree Hack', as I've been unable to come with a 
    better name.
    """
    
    def __init__(self, env, req, repos, svgrevtree):
        """Creates the internal data from the repository"""
        self.env = env
        self._repos = repos
        self._creations = []
        self._deliveries = []
        self._brings = []
        self._groups = []
        self._svgrevtree = svgrevtree
        # z-depth indexed widgets
        self._widgets = [[] for l in IRevtreeEnhancer.ZLEVELS]
        for branch in self._repos.branches().values():
            svgbranch = self._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            firstchgset = branch.oldest()
            if firstchgset:
                msg = firstchgset.changeset.message.lower()
                if msg.startswith('creates'):
                    svgbranch.svgchangeset(firstchgset).mark_first()
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
                    svgbranch.svgchangeset(lastchgset).mark_last()
        
        for branch in self._repos.branches().values():
            svgbranch = self._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            for chgset in branch.changesets():
                if chgset.prop('rth:export'):
                    svgchgset = svgbranch.svgchangeset(chgset)
                    svgchgset.set_shape('hexa')
                msg = chgset.changeset.message.lower()
                if msg.startswith('delivers'):
                    deliver = chgset.prop('rth:deliver')
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
                elif msg.startswith('imports'):
                    svgchgset = svgbranch.svgchangeset(chgset)
                    svgchgset.set_shape('Circle')
                elif msg.startswith('brings'):
                    bring = chgset.prop('rth:bring')
                    if not bring:
                        continue
                    try:
                        revisions = [int(c) for c in bring.split(',')]
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
                        self._brings.append((lchg,chgset))
                    except ValueError:
                        pass
                    except IndexError:
                        pass
        
    def build(self):
        """Build the enhanced widgets"""
        for (srcchg, dstchg) in self._creations:
            svgsrcbr = \
                self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, 
                              '#5faf5f')
            self._widgets[IRevtreeEnhancer.ZMID].append(op)
        
        for (first, last) in self._groups:
            svgbranch = \
                self._svgrevtree.svgbranch(branchname=first.branchname)
            if not svgbranch:
                continue
            fsvg = svgbranch.svgchangeset(first)
            lsvg = svgbranch.svgchangeset(last)
            group = SvgGroup(self._svgrevtree, fsvg, lsvg)
            self._widgets[IRevtreeEnhancer.ZBACK].append(group)
        
        for (srcchg, dstchg) in self._deliveries:
            svgsrcbr = \
                self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, 
                              'blue')
            self._widgets[IRevtreeEnhancer.ZMID].append(op)

        for (srcchg, dstchg) in self._brings:
            svgsrcbr = \
                self._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                self._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(self._svgrevtree, svgsrcchg, svgdstchg, 'orange')
            self._widgets[IRevtreeEnhancer.ZMID].append(op)
            
        for wl in self._widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(IRevtreeEnhancer.ZLEVELS):
            map(lambda w: w.render(), self._widgets[level])


class LogEnhancerModule(Component):
    """Revtree enhancer based on specific log messages and custom properties
    """
    
    implements(IRevtreeEnhancer)    
    
    def create(self, env, req, repos, svgrevtree):
        return LogEnhancer(env, req, repos, svgrevtree)

