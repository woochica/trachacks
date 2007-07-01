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

from revtree import IRevtreeEnhancer
from revtree.svgview import SvgOperation, SvgGroup
from trac.core import *

__all__ = ['LogEnhancer']

class SimpleContainer(object):
    """Simple container for enhancer parameters"""
    
    def __init__(self):
        pass


class LogEnhancer(Component):
    """Revtree enhancer based on specific log messages and custom properties
    This class is provided as-is, as an example
    """
    
    implements(IRevtreeEnhancer)    
    
    def create(self, env, req, repos, svgrevtree):
        """Creates the internal data from the repository"""
        enhancer = SimpleContainer()
        enhancer._repos = repos
        enhancer._creations = []
        enhancer._deliveries = []
        enhancer._brings = []
        enhancer._groups = []
        enhancer._svgrevtree = svgrevtree
        # z-depth indexed widgets: back=1, fore=2
        enhancer._widgets = ([], [], [])
        for branch in enhancer._repos.branches().values():
            svgbranch = enhancer._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            firstchgset = branch.oldest()
            if firstchgset:
                msg = firstchgset.changeset.message.lower()
                if msg.startswith('creates'):
                    svgbranch.svgchangeset(firstchgset).mark_first()
                    if branch.source():
                        (rev, path) = branch.source()
                        srcchg = enhancer._repos.changeset(rev)
                        if srcchg is None:
                            continue
                        enhancer._creations.append((srcchg, firstchgset))
            lastchgset = branch.youngest()
            if lastchgset:
                msg = lastchgset.changeset.message.lower()
                if msg.startswith('terminates'):
                    svgbranch.svgchangeset(lastchgset).mark_last()
        
        for branch in enhancer._repos.branches().values():
            svgbranch = enhancer._svgrevtree.svgbranch(branch=branch)
            if not svgbranch:
                continue
            for chgset in branch.changesets():
                if chgset.prop('st:export'):
                    svgchgset = svgbranch.svgchangeset(chgset)
                    svgchgset.set_shape('hexa')
                msg = chgset.changeset.message.lower()
                if msg.startswith('delivers'):
                    deliver = chgset.prop('st:deliver')
                    if not deliver:
                        continue
                    try:
                        revisions = [int(c) for c in deliver.split(',')]
                        revisions.sort()
                        ychg = enhancer._repos.changeset(revisions[-1])
                        if not ychg:
                            continue
                        brname = ychg.branchname
                        srcbranch = enhancer._repos.branch(brname)
                        if not srcbranch:
                            continue
                        brrevs = [c.rev for c in srcbranch.changesets()]
                        valrevs = [r for r in revisions if r in brrevs]
                        fchg = enhancer._repos.changeset(valrevs[0])
                        lchg = enhancer._repos.changeset(valrevs[-1])
                        enhancer._groups.append((fchg,lchg))
                        enhancer._deliveries.append((lchg,chgset))
                    except ValueError:
                        pass
                    except IndexError:
                        pass
                elif msg.startswith('imports'):
                    svgchgset = svgbranch.svgchangeset(chgset)
                    svgchgset.set_shape('Circle')
                elif msg.startswith('brings'):
                    bring = chgset.prop('st:bring')
                    if not bring:
                        continue
                    try:
                        revisions = [int(c) for c in bring.split(',')]
                        revisions.sort()
                        ychg = enhancer._repos.changeset(revisions[-1])
                        if not ychg:
                            continue
                        brname = ychg.branchname
                        srcbranch = enhancer._repos.branch(brname)
                        if not srcbranch:
                            continue
                        brrevs = [c.rev for c in srcbranch.changesets()]
                        valrevs = [r for r in revisions if r in brrevs]
                        fchg = enhancer._repos.changeset(valrevs[0])
                        lchg = enhancer._repos.changeset(valrevs[-1])
                        enhancer._groups.append((fchg,lchg))
                        enhancer._brings.append((lchg,chgset))
                    except ValueError:
                        pass
                    except IndexError:
                        pass

        return enhancer
                
    def build(self, enhancer):
        """Build the enhanced widgets"""
        for (srcchg, dstchg) in enhancer._creations:
            svgsrcbr = \
                enhancer._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                enhancer._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(enhancer._svgrevtree, svgsrcchg, svgdstchg, 
                              '#5faf5f')
            enhancer._widgets[2].append(op)
        
        for (first, last) in enhancer._groups:
            svgbranch = \
                enhancer._svgrevtree.svgbranch(branchname=first.branchname)
            if not svgbranch:
                continue
            fsvg = svgbranch.svgchangeset(first)
            lsvg = svgbranch.svgchangeset(last)
            group = SvgGroup(enhancer._svgrevtree, fsvg, lsvg)
            enhancer._widgets[1].append(group)
        
        for (srcchg, dstchg) in enhancer._deliveries:
            svgsrcbr = \
                enhancer._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                enhancer._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(enhancer._svgrevtree, svgsrcchg, svgdstchg, 
                              'blue')
            enhancer._widgets[2].append(op)

        for (srcchg, dstchg) in enhancer._brings:
            svgsrcbr = \
                enhancer._svgrevtree.svgbranch(branchname=srcchg.branchname)
            svgdstbr = \
                enhancer._svgrevtree.svgbranch(branchname=dstchg.branchname)
            if not svgsrcbr or not svgdstbr:
                continue
            svgsrcchg = svgsrcbr.svgchangeset(srcchg)
            svgdstchg = svgdstbr.svgchangeset(dstchg)
            op = SvgOperation(enhancer._svgrevtree, svgsrcchg, svgdstchg,
                              'orange')
            enhancer._widgets[2].append(op)
            
        for wl in enhancer._widgets:
            map(lambda w: w.build(), wl)
        
    def render(self, enhancer, level):
        """Renders the widgets, from background plane to foreground plane"""
        if level < len(enhancer._widgets):
            map(lambda w: w.render(), enhancer._widgets[level])
