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
import sha
import os

from trac.core import *
from trac.util import Markup, TracError
from trac.web import IRequestHandler
from trac.web.chrome import add_stylesheet, INavigationContributor, \
                            ITemplateProvider
from trac.web.href import Href
from trac.wiki import WikiSystem
from trac.perm import IPermissionRequestor
from revtree.model import Repository
from revtree.view  import RepositoryWidget
from revtree.repproxy import RepositoryProxy


class RevTreeStore(object):
    """User revtree properties"""
    def __init__(self, env, user, eldest, youngest):
        """Initialize the instance with default values"""
        self.env = env
        self.fields = self.get_fields()
        self.values = {}
        self.anybranch = 'All'
        self.anyauthor = 'All'
        self.revrange = None
        self.revspan = (eldest, youngest)
        self['revmin'] = str(self.revspan[0])
        self['revmax'] = str(self.revspan[1])
        self['period'] = 14
        self['limits'] = 'limperiod'
        self['branch'] = self.anybranch
        self['author'] = user or self.anyauthor
        self['btup'] = '1'
        self['hideterm'] = '1'
        self['nocache'] = ''

    def get_fields(self):
        """Returns the sequence of supported fields"""
        return [ 'revmin', 'revmax', 'period', 'branch', 'author',
                 'limits', 'btup', 'hideterm' ]
        
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

    def compute_range(self, repos):
        """Computes the range of revisions to show"""
        if self['limits'] == 'limrev':
            self.revrange = (int(self['revmin']), int(self['revmax']))
        elif self['limits'] == 'limperiod':
            period = int(self['period'])
            if period:
                self.revrange = repos.get_revisions_by_date((period, 0))
            else:
                self.revrange = self.revspan
        else:
            self.revrange = self.revspan

    def can_be_rendered(self):
        """Reports whether the revtree has enough items to produce a valid 
           representation, based on the revision range"""
        if not self.revrange:
            return False
        if self.revrange[0] == self.revrange[1]:
            return False
        return True

    def __getitem__(self, name):
        """getter (dictionary)"""
        return self.values[name]

    def __setitem__(self, name, value):
        """setter (dictionnary)"""
        self.values[name] = value


class RevisionTreeModule(Component):
    """Implements the revision tree feature"""
    
    implements(IPermissionRequestor, INavigationContributor, \
               IRequestHandler, ITemplateProvider)
    
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
        proxy = RepositoryProxy(self.repos_path)
        youngest = proxy.get_youngest_revision()
        repos = Repository(proxy)
        repos.build(self.topdir, self.propdomain, self.eldest)

        revtree = RevTreeStore(self.env, req.authname, self.eldest, 
                               youngest)
        revtree.load(req.session)
        revtree.populate(req.args)
        revtree.compute_range(repos)
        img_kind = self._get_image_kind(req)

        if revtree.can_be_rendered():
            # save the user parameters only if the tree can be rendered
            revtree.save(req.session)
            (content, properties) = \
                self._render_graph(req, repos, revtree, youngest, img_kind, \
                                   req.args.has_key('nocache'))
            # queries the repository for branches and authors if it has 
            # a newer revision than the one in the revtree
            if properties['revisions'][0] < youngest:
                branches = repos.branches().keys()
                authors = repos.authors()
            else:
                branches = properties['branches']
                authors = properties['authors']
        else:
            branches = repos.branches().keys()
            authors = repos.authors()

        branches.sort()
        authors.sort()
        branches.insert(0, revtree.anybranch)
        authors.insert(0, revtree.anyauthor)
        
        for field in revtree.fields:
            req.hdf['revtree.' + field] = revtree[field]
        req.hdf['title'] = 'Revision Tree'
        req.hdf['revtree.revisions'] = self._get_ui_revisions(revtree.revspan)
        req.hdf['revtree.branches'] = branches
        req.hdf['revtree.authors'] = authors
        req.hdf['revtree.periods'] = self._get_periods()
        
        if revtree.can_be_rendered():
            req.hdf.set_unescaped('revtree.img', content)
        else:
            req.hdf['revtree.errormsg'] = "Selected filters cannot render" \
                                          " a revision tree"
                                          
        add_stylesheet(req, 'revtree/css/revtree.css')
        proxy.cleanup()
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

    # end of Interface implementation

    def __init__(self):
        # Cache directory (reuses graphviz dir)
        self.cache_dir = self.config.get('graphviz', 'cache_dir')
        if not self.cache_dir or not os.path.exists(self.cache_dir):
            raise TracError, "cache directory is not valid"
        # Repository proxy
        if self.config.get('trac', 'repository_type') != 'svn':
            raise TracError, "revtree only supports Subversion repositories"
        self.repos_path = self.config.get('trac', 'repository_dir')
        self.topdir = self.env.config.get('revtree', 'topdir', '/')
        self.propdomain = self.env.config.get('revtree', 'domain', 'custom')
        self.eldest = int(self.env.config.get('revtree', 'revbase', '1'))
        self.format = self.env.config.get('revtree', 'format', 'auto').lower()
        self.image_engine = 'dot'
        self.periods = { 1 : 'day', 2 : '2 days', 3 : '3 days', 7: 'week',
                         14 : 'fortnight', 31 : 'month', 61 : '2 months', 
                         91 : '3 months', 366 : 'year', 0 : 'all' }

    def _get_image_kind(self, req):
        """Reports whether to produce PNG or SVG output
           There is no way to know whether the user agent supports SVG
           so use a hardcoded recognition scheme"""
           
        def get_browser_version(agent):
            try:
                (name, version) = agent.split('/')
                if version:
                    v = version.split('.')
                    if len(v) > 1:
                        vlist = map(int, v) + [0] * 3
                        version = 0
                        for v in vlist[0:3]:
                            version *= 100
                            version += v
                        return (name.lower(), version)
            except ValueError:
                pass
            return (None, None)
            
        if self.format in ['png', 'svg']:
            return self.format
        if self.format == 'auto':
            agentstr = req.get_header('user-agent')
            if agentstr:
                info = agentstr.split()
                (name, version) = get_browser_version(info[0])
                if name:
                    if name == 'opera' and version >= 90000:
                        return 'svg'
                    if name == 'mozilla' and version >= 50000:
                        (name, version) = get_browser_version(info[-1])
                        if name == 'firefox' and version >= 10500:
                            return 'svg'
                        if name in ['camino'] and version >= 10002:
                            return 'svg'
        # always fall back to PNG
        return 'png'
        
    def _get_periods(self):
        """Generates a list of periods"""
        values = self.periods
        periods = []
        days = values.keys()
        days.sort()
        for d in days:
            periods.append( { 'value' : d, 'label' : values[d] } )
        return periods

    def _get_cache_name(self, revtree):
        """Generates a unique filename for the current revtree"""
        id = "%d-%d-%s-%s-%d-%d" % (revtree.revrange[0], \
                                    revtree.revrange[1], \
                                    revtree['branch'] or ' ', \
                                    revtree['author'] or ' ', \
                                    revtree['btup'] != '0' and 1 or 0, \
                                    revtree['hideterm'] != '0' and 1 or 0)
        sha_key  = sha.new(id).hexdigest()
        img_name = '%s.revtree' % (sha_key)
        img_path = os.path.join(self.cache_dir, img_name)
        return img_path

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

    def _render_graph(self, req, repos, revtree, youngest, img_kind, rebuild):
        """Renders revtree graph (tests cache status and generates a new image
           if not found)"""
        cache_file = self._get_cache_name(revtree)
        create = True
        headers = ['revisions', 'branches', 'authors', 'image' ]
        props = {}
        
        if not rebuild and os.path.exists(cache_file):
            try:
                cache = open(cache_file, 'r')
                if not cache:
                    raise IOError
                for header in headers:
                    (key, value) = cache.readline().split(':')
                    if key != header:
                        raise ValueError
                    props[header] = value.strip().split(',')    
                cache.readline()
                content = '\n'.join(cache.readlines())
                cache.close()
                image = os.path.join(self.cache_dir, "%s.%s.%s" % \
                                      (props['image'][0], self.image_engine,
                                       img_kind))
                if os.path.exists(image):
                    create = False
                else:
                    self.env.log.debug("Image %s is missing" % image)
            except ValueError:
                self.log.warn('Unable to load graph from cache file %s', \
                              cache_file)
                if cache:
                    cache.close()
                self.log.warn('Unable to load graph from cache file %s', \
                              cache_file)
                os.unlink(cache_file)

        if create:
            (content, revisions, branches, authors) = \
                self._generate_graph(req, repos, revtree, img_kind)
            props['revisions'] = (str(youngest), \
                                  str(revisions[0]), str(revisions[1]))
            props['branches'] = branches
            props['authors'] = authors
            image_re = re.compile('<object data="(.*?)"')
            mo = image_re.search(content)
            if mo:
                props['image'] = (mo.group(1), )
            else:
                self.env.log.warn('Unable to find image uid in graphviz ' \
                                  'content: %s' % content)
                props['image'] = None
            try:
                cache = open(cache_file, 'w')
                if not cache:
                    raise IOError
                for header in headers:
                    if props.has_key(header) and props[header]:
                        prop = ','.join(filter(None, props[header]))
                        cache.write("%s: %s\n" % (header, prop))
                cache.write("\n%s\n" % content)
                cache.close() 
            except (ValueError, IOError):
                self.log.warn('Unable to save graph in cache file %s', \
                              cache_file)
            except TypeError:
                raise TracError, \
                      "Error rendering the rev tree (type: %s)" % header
        return (content, props)

    def _generate_graph(self, req, repos, revtree, img_kind): 
        """Generates the revtree image"""
        trunks = self.env.config.get('revtree', 'trunks', '/trunk').split(' ')
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
        if revisions[-1] != str(revtree.revspan[0]):
            revisions.append(str(revtree.revspan[0]))
        brnames = [bn for bn in repos.branches().keys() if bn not in trunks]
        brnames.sort()
        branches = []
        authors = repos.authors()
        gvizbranches = None
        brfilter = None
        if revtree['branch'] != revtree.anybranch:
            brfilter = revtree['branch']
        authfilter = None
        if revtree['author'] != revtree.anyauthor:
            authfilter = revtree['author']
        for b in brnames:
            if brfilter and brfilter != b:
                continue
            if authfilter and authfilter not in repos.branch(b).authors():
                continue
            branches.append(b)
        if brfilter or authfilter:
            gvizbranches = trunks
            gvizbranches.extend(branches)
        repwdgt = RepositoryWidget(self.env, repos, req.base_url)
        repwdgt.build(revtree.revrange, gvizbranches, authors)        
        gviz = repwdgt.render(revtree['btup'] != '0', 
                              revtree['hideterm'] != '0', 
                              img_kind == 'svg')
        macro = 'graphviz.%s/%s' % (self.image_engine, img_kind)
        wiki = WikiSystem(self.env)
        content = None
        for macro_provider in wiki.macro_providers:
            if macro in list(macro_provider.get_macros()):
                content = macro_provider.render_macro(req, macro, gviz)
                break
        if not content:
            raise TracError, "GraphViz (%s) processor not found" % macro
        revrange = repos.revision_range()
        return (content, revrange, brnames, authors)

