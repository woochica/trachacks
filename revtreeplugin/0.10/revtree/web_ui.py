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

import re
import os
import time

from trac.core import *
from trac.util import Markup, TracError
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, INavigationContributor, \
                            ITemplateProvider
from trac.web.href import Href
from trac.wiki import WikiSystem
from trac.perm import IPermissionRequestor
from revtree import Repository, SvgRevtree, ChangesetEmptyRange
from revtree.enhancer import Enhancer

class RevtreeStore(object):
    """User revtree properties"""
    
    def __init__(self, env, authname, revspan, timebase, style):
        """Initialize the instance with default values"""
        self.env = env
        self.fields = self.get_fields()
        self.values = {}
        self.anybranch = 'All'
        self.anyauthor = 'All'
        self.revrange = None
        self.timerange = None
        self.revspan = revspan
        self.authname = authname
        self.timebase = timebase
        self['revmin'] = str(self.revspan[0])
        self['revmax'] = str(self.revspan[1])
        self['period'] = 14
        self['limits'] = 'limperiod'
        self['treestyle'] = style
        self['branch'] = self.anybranch
        self['author'] = authname or self.anyauthor
        self['hideterm'] = '1'

    def get_fields(self):
        """Returns the sequence of supported fields"""
        return [ 'revmin', 'revmax', 'period', 'branch', 'author',
                 'limits', 'hideterm', 'treestyle' ]
        
    def load(self, session):
        """Load user parameters from a previous session"""
        for field in self.fields:
            key = 'revtree.%s' % field
            if session.has_key(key):
                self[field] = session.get(key, '')

    def save(self, session):
        """Store user parameters"""
        for field in self.fields:
            key = 'revtree.%s' % field
            if self[field]:
                session[key] = self[field]
            else:
                if session.has_key(key):
                    del session[key]

    def populate(self, values):
        """Populate the revtree from the request"""
        for name in [name for name in values.keys() if name in self.fields]:
            genkey = 'any%s' % name
            if self.__dict__.has_key(genkey):
                if self.__dict__[genkey] == values.get(name, ''):
                    self[name] = self.__dict__[genkey]
                    continue
            self[name] = values.get(name, '')
        for name in [name for name in values.keys() if name[9:] in self.fields
                     and name.startswith('checkbox_')]:
            if not values.has_key(name[9:]):
                self[name[9:]] = '0'

    def compute_range(self):
        """Computes the range of revisions to show"""
        if self['limits'] == 'limrev':
            self.revrange = (int(self['revmin']), int(self['revmax']))
        elif self['limits'] == 'limperiod':
            period = int(self['period'])
            if period:
                now = self.timebase
                self.timerange = (now-period*86400, now)
                return
        self.revrange = self.revspan

    def can_be_rendered(self):
        """Reports whether the revtree has enough items to produce a valid 
           representation, based on the revision range"""
        if self.timerange:
            return True
        if self.revrange and (self.revrange[0] < self.revrange[1]):
            return True
        return False
        
    def get_authors(self):
        """Returns the list of selected authors, or None if no author filter
        is selected"""
        if self.anyauthor in self['author']:
            return None
        return [self['author']]
        #return [a for a in self['author'] if a != self.anyauthor]

    def get_branches(self):
        """Returns the list of selected branches, or None if no branch filter 
        is selected"""
        if self.anybranch in self['branch']:
            return None
        return [self['branch']]
        #return [b for b in self['branch'] if b != self.anybranch]
        
    def get_hidetermbranch(self):
        return int(self['hideterm']) == 1
        
    def get_style(self):
        return self['treestyle']
        
    def __getitem__(self, name):
        """getter (dictionary)"""
        return self.values[name]

    def __setitem__(self, name, value):
        """setter (dictionnary)"""
        self.values[name] = value


class RevtreeModule(Component):
    """Implements the revision tree feature"""
    
    implements(IPermissionRequestor, INavigationContributor, \
               IRequestHandler, ITemplateProvider)
    
    PERIODS = { 1 : 'day', 2 : '2 days', 3 : '3 days', 7: 'week',
                14 : 'fortnight', 31 : 'month', 61 : '2 months', 
                91 : '3 months', 366 : 'year', 0 : 'all' }
    
    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['REVTREE_VIEW']
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'revtree'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('REVTREE_VIEW'):
            return
        yield ('mainnav', 'revtree', Markup('<a href="%s">Rev Tree</a>',
                                             self.env.href.revtree()))

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/revtree/?', req.path_info) is not None

    def process_request(self, req):
        req.perm.assert_permission('REVTREE_VIEW')
            
        revstore = RevtreeStore(self.env, req.authname, \
                                (self.oldest, self.youngest),
                                self.timebase or int(time.time()), 
                                self.style)
        revstore.load(req.session)
        revstore.populate(req.args)
        revstore.compute_range()

        # fill in the HDF 
        for field in revstore.fields:
            req.hdf['revtree.' + field] = revstore[field]
        req.hdf['title'] = 'Revision Tree'
        req.hdf['revtree.periods'] = self._get_periods()

        try:
            if not revstore.can_be_rendered():
                raise ChangesetEmptyRange
                
            repos = Repository(self.env, req.authname)
            repos.build(self.bcre, revstore.revrange, revstore.timerange)

            (revisions, branches, authors) = \
                self._select_parameters(repos, req, revstore)
            filename = self._get_filename()
                                        
            svgrevtree = SvgRevtree(self.env, repos, self.urlbase)
            enhancer = Enhancer(repos, svgrevtree)
            svgrevtree.add_enhancer(enhancer)
            #self.env.log.debug("REVISIONS %s" % [revstore.revrange])
            #self.env.log.debug("BRANCH %s" % revstore.get_branches())
            #self.env.log.debug("AUTHOR %s" % revstore.get_authors())
            #self.env.log.debug("HIDE %s" % revstore.get_hidetermbranch())
            svgrevtree.create(revstore.revrange, revstore.get_branches(), 
                              revstore.get_authors(), 
                              revstore.get_hidetermbranch(), 
                              revstore.get_style())
            svgrevtree.build()
            svgrevtree.render()
            svgrevtree.save(os.path.join(self.cache_dir, filename))
            extent = svgrevtree.extent()
            extent = ((extent[0]*self.scale)/100,(extent[1]*self.scale)/100)
            # FIXME
            #extent = (800,(extent[1]*600)/extent[0])
                    
            if not self.cache_url.startswith('/'):
                src = req.href.chrome("site/cache/%s" % filename)
            else:
                src = "%s/%s" % (self.cache_url, filename)
            req.hdf['revtree.svg.src'] = src
            (w,h) = extent
            #(w,h) = (900, (900*h)/w)
            req.hdf['revtree.svg.width'] = "%dpx" % w
            req.hdf['revtree.svg.height'] = "%dpx" % h
            
            # create and order the drop-down list content, starting with the
            # global values 
            branches = repos.branches().keys()
            authors = repos.authors()
            branches.sort()
            authors.sort()
            branches.insert(0, revstore.anybranch)
            authors.insert(0, revstore.anyauthor)
            
            # save the user parameters only if the tree can be rendered
            revstore.save(req.session)
            
        except ChangesetEmptyRange:
            req.hdf['revtree.errormsg'] = "Selected filters cannot render" \
                                          " a revision tree"
            # restore default parameters
            repos = Repository(self.env, req.authname)
            repos.build(self.bcre, revrange=(self.oldest,self.youngest))
            branches = repos.branches().keys()
            branches.sort()
            branches.reverse()
            authors = repos.authors()
            authors.sort()
            
        revrange = repos.revision_range()
        revisions = self._get_ui_revisions(revrange)

        # fill in the HDF 
        req.hdf['revtree.revmin'] = revrange[0]
        req.hdf['revtree.revmax'] = revrange[1]
        req.hdf['revtree.revisions'] = revisions
        req.hdf['revtree.branches'] = branches
        req.hdf['revtree.authors'] = authors
                                                                               
        add_stylesheet(req, 'revtree/css/revtree.css')
        return 'revtree.cs', None

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('revtree', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # end of interface implementation

    def __init__(self):
        if self.config.get('trac', 'repository_type') != 'svn':
            raise TracError, "Revtree only supports Subversion repositories"
        bre = self.config.get('revtree', 'branch_re',
                  r'^(?P<branch>branches/[^/]+|trunk|data)'
                  r'(/(?P<path>.*))?$')
        self.bcre = re.compile(bre)
        self.urlbase = self.config.get('trac', 'base_url')
        self.cache_dir = self.config.get('revtree', 'cache_dir', '%s/cache' \
                                            % self.env.get_htdocs_dir())
        self.cache_url = self.config.get('revtree', 
                                         'cache_url', '').encode('ascii')
        self.trunks = self.env.config.get('revtree', 'trunks', 
                                          'trunk').split(' ')
        self.scale = self.env.config.get('revtree', 'scale', '50')
        if (self.scale < 1) or (self.scale>500):
            self.scale = 50 
        
        if not self.cache_dir or not os.path.exists(self.cache_dir):
            raise TracError("Cache directory is not valid: %s" % \
                            self.cache_dir)
        if not self.urlbase:
            raise TracError, "Base URL not defined"
        repos = self.env.get_repository()
        self.oldest = int(self.env.config.get('revtree', 'revbase', 
                                              repos.get_oldest_rev()))
        self.youngest = repos.get_youngest_rev()
        if self.config.getbool('revtree', 'reltime', True):
            self.timebase = repos.get_changeset(self.youngest).date
        else:
            self.timebase = None
        self.style = self.config.get('revtree', 'style', 'compact')
        if self.style not in [ 'compact', 'timeline']:
            raise TracError, "Unsupported style: %s" % self.style

    def _get_periods(self):
        """Generates a list of periods"""
        values = RevtreeModule.PERIODS
        periods = []
        days = values.keys()
        days.sort()
        for d in days:
            periods.append( { 'value' : d, 'label' : values[d] } )
        return periods

    def _get_filename(self):
        """Generates a unique filename"""
        return '%d.svg' % int(time.time())

    def _get_ui_revisions(self, revspan):
        """Generates the list of displayable revisions"""
        (revmin, revmax) = revspan
        allrevisions = range(revmin, revmax+1)
        allrevisions.sort()
        revs = [c for c in allrevisions]
        revs.reverse()
        revisions = []
        for rev in revs:
            if len(revisions) > 40:
                if int(rev)%20:
                    continue
            elif len(revisions) > 10:
                if int(rev)%10:
                    continue
            revisions.append(str(rev))
        if revisions[-1] != str(revmin):
            revisions.append(str(revmin))
        return revisions

    def _select_parameters(self, repos, req, revstore):
        """ """
        revs = [c for c in repos.changesets()]
        revs.reverse()
        revisions = []
        for rev in revs:
            if len(revisions) > 40:
                if int(rev)%20:
                    continue
            elif len(revisions) > 10:
                if int(rev)%10:
                    continue
            revisions.append(rev)
        if revisions[-1] != str(revstore.revspan[0]):
            revisions.append(str(revstore.revspan[0]))
        brnames = [bn for bn in repos.branches().keys() \
                      if bn not in self.trunks]
        brnames.sort()
        branches = []
        authors = repos.authors()
        vbranches = None
        brfilter = None
        if revstore['branch'] != revstore.anybranch:
            brfilter = revstore['branch']
        authfilter = None
        if revstore['author'] != revstore.anyauthor:
            authfilter = revstore['author']
        for b in brnames:
            if brfilter and brfilter != b:
                continue
            if authfilter and authfilter not in repos.branch(b).authors():
                continue
            branches.append(b)
        if brfilter or authfilter:
            vbranches = self.trunks
            vbranches.extend(branches)
        return ((revisions[0], revisions[-1]), vbranches, authors)
