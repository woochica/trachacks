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

from random import randrange, seed
from revtree.model import Changeset, Branch, Repository 


class ChangesetWidget(object):
    """ Graphviz generator for changesets """

    def __init__(self, grapher, changeset):
        # Environment
        self.env = grapher.env
        # Graphviz data builder
        self._grapher = grapher
        # Changeset object
        self._changeset = changeset
        # Operation widget (represents the command that created the revision)
        self._opwidget = None

        repository = self._grapher.repository()
        if changeset.references:
            refs = [repository.changeset(rev) for rev in changeset.references]
            self._opwidget = OperationWidget(self.env, tuple(refs), changeset)
        # kludge as there's no copy info in text file (to be removed in final v.)
        elif changeset.operation == Changeset.CREATE:
            changesets = []
            for trunk in grapher.trunks:
                chgs = self._grapher.repository().branch(trunk).changesets()
                changesets.extend(chgs)
            revs = [chg.revision for chg in changesets]
            revs.sort()
            revs.reverse()
            for r in revs:
                if r < changeset.revision:
                    srcchg = self._grapher.repository().changeset(r)
                    self._opwidget = OperationWidget(self.env, (srcchg, ), \
                                                     changeset)
                    break

    def id(self):
        """ Returns the unique identifier of the changeset, based on the
            revision number """
        return self._changeset.revision

    def operation_widget(self):
        """ Provides the operation widget, i.e. the widget representation
            of the operation (command) that created the revision """
        return self._opwidget

    def forecolor(self):
        """ Provides the forecolor of the widget """
        colormap = ['']*8
        colormap[Changeset.NONE] = ('defaultcolor', None)
        colormap[Changeset.IMPORT] = ('importcolor', None)
        colormap[Changeset.CREATE] = ('createcolor', '#00af00')
        colormap[Changeset.BRING] = ('bringcolor', '#bf7f00')
        colormap[Changeset.DELIVER] = ('delivercolor', '#0000af')
        colormap[Changeset.FIX] = ('fixcolor', '#3faf00')
        colormap[Changeset.REF] = ('refcolor', None)
        colormap[Changeset.KILL] = ('killcolor', '#ff0000')
        (colorname, defcolor) = colormap[self._changeset.operation or \
                                         Changeset.NONE]
        color = self.env.config.get('revtree', colorname, defcolor)
        if not color:
            return self._grapher.branch_widget(rev=self.id()).forecolor()
        return color

    def backcolor(self):
        """ Provides the background color of the widget """
        return self._grapher.branch_widget(rev=self.id()).backcolor()

    def shape(self):
        """ Provides the shape of the widget """
        if self._changeset.operation in [ Changeset.CREATE, Changeset.KILL ]:
            return "doublecircle"
        if self._changeset.export:
            return "diamond"
        if self._changeset.importlabel:
            return "Mcircle"
        return "circle"

    def style(self):
        """ Provides the style of the widget """
        if self._changeset.operation in [ Changeset.FIX ]:
            return "bold"
        return "none"

    def render(self):
        """ Returns a Graphviz representation of the widget """
        url = "%s/changeset/%d" % (self._grapher.urlbase(), \
                                   self._changeset.revision)
        log = self._changeset.log.replace('[[BR]]',' ').replace('\n',' ')
        log = log.replace('"',"'").replace('  ',' ')
        words = log.split(' ')
        msg = ''
        for word in words:
            if len(msg)+len(word) < 75:
                msg = "%s %s " % (msg, word)
            else:
                msg = "%s..." % msg
                break
        tooltip = "[%s] %s" % (self._changeset.author, msg)
        bwdgt = self._grapher.branch_widget(branchname=self._changeset.branchname)
        groupname = bwdgt.id()
        str = '%d [URL="%s",tooltip="%s",color="%s",fillcolor="%s",' \
              'shape=%s,width=0.2,height=0.2,margin="0.02,0.02",group="g%s"]' % \
                (self.id(), url, tooltip, self.forecolor(), self.backcolor(), \
                 self.shape(), groupname)
        return str


class BranchWidget(object):
    """ Graphviz generator for branches """

    def __init__(self, grapher, branch):
        # Environment
        self.env = grapher.env
        # Graphviz data builder
        self._grapher = grapher
        # Branch object
        self._branch = branch
        # Unique identifier of the branch (based on the name)
        self._id = branch.name().replace('/','_').replace('-','_')
        # Edge color
        self.transcolor = self.env.config.get('revtree', 'transcolor', \
                                              '#7f7f7f')
        # Background color
        if branch.name() in grapher.trunks:
            self._backcolor = self.env.config.get('revtree', 'trunkcolor', \
                                                  '#cfcfcf')
        else:
            self._backcolor = self._randcolor()

    def forecolor(self):
        """ Returns the foreground color of the widget """
        return self.env.config.get('revtree', 'outlinecolor', 'black')

    def backcolor(self):
        """ Returns the background color of the widget """
        return self._backcolor

    def id(self):
        """ Returns the unique identifier of the branch, derived from the
            path """
        return self._id

    def branch(self):
        """ Returns the branch object """
        return self._branch

    def render(self, revrange=None, reverse=False):
        """ Returns a Graphviz representation of the widget """
        changesets = self._branch.changesets()
        inrngchgs = [c for c in changesets if self._inrange(c.revision, revrange)]
        items = ["%s" % self._grapher.changeset_widget(c.revision).render() \
                  for c in inrngchgs]
        if not items:
            return ''
        representation = '%s;\n' % ';\n  '.join(items)
        if len(self._branch) > 1:
            revisions = ["%d" % chg.revision for chg in inrngchgs]
            chgstr = ' -> '.join(revisions)
            if chgstr:
                transitions = '%s [color="%s"];' % (chgstr, self.transcolor)
                representation += "  %s\n" % transitions
        
        if len(inrngchgs) > 1 or inrngchgs[0].operation != Changeset.KILL:
            url = "%s/browser%s%s" % (self._grapher.urlbase(), 
                                      self._branch.name(), 
                                      inrngchgs[-1].topdir)
            if inrngchgs[-1].operation == Changeset.KILL and \
               len(inrngchgs) > 1:
                url += "?rev=%d" % int(inrngchgs[-2].revision)
            tooltip = "View %s source code" % self._branch.name()
            link = 'URL="%s",tooltip="%s"' % (url, tooltip)
        else:
            link = 'tooltip="Terminated branch"'
        label = '%s [rank="max",%s,color="%s",label="%s",' \
                'fillcolor="%s",group="g%s",label="%s",shape=box,height=0.3];' % \
                  (self.id(), link, self.transcolor,  self._branch.name(), \
                   self.backcolor(), self.id(), self._branch.name())
        if reverse:
            if revrange:
                revchangesets = changesets
                revchangesets.reverse()
                for c in revchangesets:
                    if c.revision <= revrange[1]:
                        maxrev = c.revision
                        break
            else:
                maxrev = changesets[-1].revision
            ledge = '%d -> %s [dir=none,style=dotted,color="%s"];' % \
                      (maxrev, self.id(), self.transcolor)
        else:
            if revrange:
                for c in changesets:
                    if c.revision >= revrange[0]:
                        minrev = c.revision
                        break
            else:
                minrev = changesets[0].revision
            ledge = '%s -> %d [dir=none,style=dotted,color="%s"];' % \
                      (self.id(), minrev, self.transcolor)
        representation += "  %s\n  %s\n" % (label, ledge)
        return representation

    def is_visible(self, revrange):
        items = [c for c in self._branch.changesets() \
                 if self._inrange(c.revision, revrange)]
        return items and True or False

    def _randcolor(self):
        """ Generates a random pastel color and returns it as a string """
        rand = "%03d" % randrange(1000)
        return "#%02x%02x%02x" % \
          (128+14*int(rand[0]), 128+14*int(rand[1]), 128+14*int(rand[2]))

    def _inrange(self, rev, revrange):
        """ Reports whether a revision is in a range """
        if not revrange:
            return True
        if rev < revrange[0] or rev > revrange[1]:
            return False
        return True


class OperationWidget(object):
    """ Graphviz generator for operations """

    def __init__(self, env, src, dst):
        if not isinstance(src, tuple):
            raise TypeError, "source changeset should be a tuple"
        # Environment
        self.env = env
        # Source changeset (initial end point of the changeset)
        self._src = src
        # Destination changeset (final end point of the changeset)
        self._dst = dst
        # 'Bring' color
        self.bringcolor = self.env.config.get('revtree', 'bringcolor', \
                                               '#ff8000')
        # 'Deliver' color
        self.delivercolor = self.env.config.get('revtree', 'delivercolor', \
                                                '#0080d0')
        # 'Create' color
        self.createcolor = self.env.config.get('revtree', 'createcolor', \
                                               '#00ff00')

    def sources(self):
        """ Returns the source changesets of the operation (as a tuple)"""
        return self._src

    def destination(self):
        """ Returns the destination changeset of the operation """
        return self._dst

    def render(self, revrange=None, reverse=False):
        """ Returns a Graphviz representation of the widget """
        if revrange:
            src = [chg for chg in self._src if \
                       chg.revision >= revrange[0] and
                       chg.revision <= revrange[1] ]
        else:
            src = self._src
        if not src:
            return ''
        if self._dst.operation == Changeset.BRING:
            return '%d -> %d [constraint=false,style=solid,color="%s"];' % \
                  (src[0].revision, self._dst.revision, self.bringcolor)
        if self._dst.operation == Changeset.DELIVER:
            if len(src) > 1:
                if reverse:
                    (reva, revb) = (src[0].revision, src[-1].revision)
                else:
                    (reva, revb) = (src[-1].revision, src[0].revision) 
                return '%d -> %d [constraint=false,style=dashed,color="%s",' \
                                  'arrowhead=none,arrowtail=none];\n' \
                       '%d -> %d [constraint=false,style=solid,color="%s"];' % \
                       (reva, revb, self.delivercolor,
                        src[-1].revision, self._dst.revision, self.delivercolor)
            else:
                return '%d -> %d [constraint=false,style=solid,color="%s"];' % \
                      (src[0].revision, self._dst.revision, self.delivercolor)
        if self._dst.operation == Changeset.CREATE:
            return '%d -> %d [constraint=true,style=solid,color="%s"];' % \
                  (src[0].revision, self._dst.revision, self.createcolor)
        return ''


class RepositoryWidget(object):
    """ Graphviz generator of a Subversion repository """

    def __init__(self, env, repos, urlbase):
        # Environment
        self.env = env
        # URL base of the repository
        self._urlbase = urlbase
        # Repository instance
        self._repos = repos
        # Dictionnary of branch widgets (branches as keys)
        self._branch_widgets = {}
        # Dictionnary of changeset widgets (changesets as keys)
        self._changeset_widgets = {}
        # Revisions range
        self._revrange = None
        # Trunk branches
        trunks = self.env.config.get('revtree', 'trunks', '/trunk')
        self.trunks = trunks.split(' ')
        # Init color generator with a predefined value
        seed(0)

    def repository(self):
        """ Returns the repository instance """
        return self._repos

    def urlbase(self):
        """ Returns the repository URL """
        return self._urlbase

    def changeset_widget(self, rev):
        """ Return the repository instance """
        c = self._repos.changeset(rev)
        return self._changeset_widgets[c]

    def branch_widget(self, rev=None, branchname=None):
        """ Returns a branch widget, based on the revision number or the 
            branch id """
        branch = None
        if rev:
            chg = self._repos.changeset(rev)
            branch = self._repos.branch(chg.branchname)
        elif branchname:
            branch = self._repos.branch(branchname)
        if not branch:  
            return None
        return self._branch_widgets[branch]

    def build(self, revisions=None, branches=None, authors=None):
        """ Builds the graph """
        self._revrange = revisions
        for b in self._repos.branches().values():
            if branches and b.name() not in branches:
                continue
            if authors:
                if not [a for a in authors for x in b.authors() if a == x]:
                    continue
            branchwdgt = BranchWidget(self, b)
            for c in b.changesets():
                if self._revrange:
                    if c.revision < self._revrange[0] or \
                       c.revision > self._revrange[1]:
                       continue 
                chgwdgt = ChangesetWidget(self, c)
                self._changeset_widgets[c] = chgwdgt
            self._branch_widgets[b] = branchwdgt

    def render(self, reverse=False):
        """ Returns the graphviz data """
        gviz = 'digraph versiontree {\n'
        gviz += '  graph [fontsize=9,rankdir="%s"]\n' % \
                (reverse and "BT" or "TB")
        gviz += '  node [fontsize=9,style=filled,' \
                'margin="0.05,0.05"]\n'
        branchnames = []
        for bwdgt in self._branch_widgets.values():
            gviz += '  %s\n' % bwdgt.render(self._revrange, reverse)
            brname = bwdgt.branch().name()
            if brname not in branchnames:
                branchnames.append(brname)
        rankbranches = [brwdgt.id() for brwdgt in self._branch_widgets.values() \
                        if brwdgt.is_visible(self._revrange)]
        gviz += '{ rank = same; %s }' % '; '.join(rankbranches)
        for cwdgt in self._changeset_widgets.values():
            if self._revrange:
                (rmin, rmax) = self._revrange
                revision = cwdgt.id()
                if revision < rmin or revision > rmax:
                    continue
            opwdgt = cwdgt.operation_widget()
            if opwdgt:
                srcnames = [src.branchname for src in opwdgt.sources()]
                if [name for name in branchnames \
                    for srcname in srcnames if name == srcname]:
                        op = opwdgt.render(self._revrange, reverse)
                        if op:
                            gviz += '  %s\n' % op
        gviz += '\n}\n'
        return gviz

