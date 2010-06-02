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

import re
import os
import time

from genshi import Markup
from genshi.builder import tag
from revtree.api import EmptyRangeError, RevtreeSystem
from revtree.model import Repository
from trac.config import Option, IntOption, BoolOption, ListOption, \
                        Section, ConfigurationError
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.util import TracError
from trac.util.datefmt import format_datetime, pretty_timedelta, to_timestamp
from trac.web import IRequestFilter, IRequestHandler
from trac.web.chrome import add_ctxtnav, add_script, add_stylesheet, \
                            INavigationContributor, ITemplateProvider
from trac.web.href import Href
from trac.wiki import wiki_to_html, WikiSystem

__all__ = ['RevtreeModule']

class RevtreeStore(object):
    """User revtree properties"""
    
    FIELDS = ( 'revmin', 'revmax', 'period', 'branch', 'author',
               'limits', 'showdel', 'style' )
    
    def __init__(self, env, authname, revspan, timebase, style):
        """Initialize the instance with default values"""
        self.env = env
        self.values = {}
        self.revrange = None
        self.timerange = None
        self.revspan = revspan
        self.authname = (authname != 'anonymous') and authname or None
        self.timebase = timebase
        self['revmin'] = str(self.revspan[0])
        self['revmax'] = str(self.revspan[1])
        self['period'] = '31'
        self['limits'] = 'limperiod'
        self['style'] = style
        self['branch'] = None
        self['author'] = self.authname
        self['showdel'] = None

    def __getitem__(self, name):
        """Getter (dictionary)"""
        return self.values[name]
   
    def __setitem__(self, name, value):
        """Setter (dictionary)"""
        self.values[name] = value
        
    def load(self, session):
        """Load user parameters from a previous session"""
        for field in RevtreeStore.FIELDS:
            key = 'revtree.%s' % field
            if session.has_key(key):
                self[field] = session.get(key, '')

    def save(self, session):
        """Store user parameters"""
        for field in RevtreeStore.FIELDS:
            key = 'revtree.%s' % field
            if self[field]:
                session[key] = str(self[field])
            else:
                if session.has_key(key):
                    del session[key]
                    
    def clear(self, session):
        """Remove all the revtree data from the user session"""
        for key in filter(lambda k: k.startswith('revtree'), session.keys()):
            del session[key]
        self.env.log.debug('Revtree data removed from user session')
            
    def populate(self, values):
        """Populate the store from the request"""
        for name in filter(lambda v: v in RevtreeStore.FIELDS, values.keys()):
            self[name] = values.get(name, '')
        # checkboxes need to be postprocessed
        self['showdel'] = values.has_key('showdel') and values['showdel']

    def compute_range(self, timebase):
        """Computes the range of revisions to show"""
        self.revrange = self.revspan
        if self['limits'] == 'limrev':
            self.revrange = (int(self['revmin']), int(self['revmax']))
        elif self['limits'] == 'limperiod':
            period = int(self['period'])
            if period:
                now = timebase
                self.timerange = (now-period*86400, now)

    def can_be_rendered(self):
        """Reports whether the revtree has enough items to produce a valid 
           representation, based on the revision range"""
        if self.timerange:
            return True
        if self.revrange and (self.revrange[0] < self.revrange[1]):
            return True
        return False
                
    def get_values(self):
        """Returns a dictionary of the stored values"""
        return self.values        


class FloatOption(Option):
    """Descriptor for float configuration options.
       Option for real number is missing in Trac
    """
    
    def accessor(self, section, name, default=''):
        """Return the value of the specified option as float.
        
        If the specified option can not be converted to a float, a
        `ConfigurationError` exception is raised.
        
        Valid default input is a string or a float. Returns an float.
        """
        value = section.get(name, default)
        if not value:
            return 0.0
        try:
            return float(value)
        except ValueError:
            raise ConfigurationError('expected real number, got %s' % \
                                     repr(value))

class ChoiceOption(Option):
    """Descriptor for choice configuration options."""

    def __init__(self, section, name, default=None, choices='', doc=''):
        Option.__init__(self, section, name, default, doc)
        self.choices = filter(None, [c.strip() for c in choices.split(',')])

    def accessor(self, section, name, default):
        value = section.get(name, default)
        if value not in self.choices:
            raise ConfigurationError('expected a choice among "%s", got %s' % \
                                     (', '.join(self.choices), repr(value)))
        return value

    
class RevtreeModule(Component):
    """Implements the revision tree feature"""
    
    implements(IPermissionRequestor, INavigationContributor, \
               IRequestFilter, IRequestHandler, ITemplateProvider)
             
    # Timeline ranges
    PERIODS = { 1: 'day', 2: '2 days', 3: '3 days', 5: '5 days', 7:'week',
                14: 'fortnight', 31: 'month', 61: '2 months', 
                91: 'quarter', 183: 'semester', 366: 'year', 0: 'all' }
  
    # Configuration Options
    branchre = Option('revtree', 'branch_re',
        r'^(?:(?P<branch>trunk|(?:branches|sandboxes|vendor)/'
        r'(?P<branchname>[^/]+))|'
        r'(?P<tag>tags/(?P<tagname>[^/]+)))(?:/(?P<path>.*))?$',
        doc = """Regular expression to extract branches from paths""")
    
    abstime = BoolOption('revtree', 'abstime', 'true',
        doc = """Timeline filters start on absolute time or on the youngest
                 revision.""")

    contexts = ListOption('revtree', 'contexts',
        doc = """Navigation contexts where the Revtree item appears.
                 If empty, the Revtree item appears in the main navigation
                 bar.""")
                 
    trunks = ListOption('revtree', 'trunks',
        doc = """Branches that are considered as trunks""")
    
    oldest = IntOption('revtree', 'revbase', '1',
        doc = """Oldest revision to consider (older revisions are ignored)""")
    
    style = ChoiceOption('revtree', 'style', 'compact', 'compact,timeline',
        doc = """Revtree style, 'compact' or 'timeline'""")
        
    scale = FloatOption('revtree', 'scale', '1',
        doc = """Default rendering scale for the SVG graph""")
        
    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['REVTREE_VIEW']
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'revtree'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('REVTREE_VIEW'):
            return
        if self.contexts:
            return
        yield ('mainnav', 'revtree', 
               tag.a('Rev Tree', href=req.href.revtree()))

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.perm.has_permission('REVTREE_VIEW'):
            url_parts = filter(None, req.path_info.split(u'/'))
            if url_parts and (url_parts[0] in self.contexts):
                add_ctxtnav(req, 'Revtree' % self.contexts, 
                            href=req.href.revtree())
        return (template, data, content_type)

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/revtree(_log)?(?:/([^/]+))?', req.path_info)
        if match:
            if match.group(1):
                req.args['logrev'] = match.group(2)
            return True

    def process_request(self, req):
        req.perm.assert_permission('REVTREE_VIEW')
            
        if req.args.has_key('logrev'):
            return self._process_log(req)
        else:
            return self._process_revtree(req)

    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('revtree', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    # end of interface implementation
            
    def __init__(self):
        """Reads the configuration and run sanity checks"""
        self.env.log.debug('Revtree RE: %s' % self.branchre)
        self.bcre = re.compile(self.branchre)
        self.rt = RevtreeSystem(self.env)

    def _process_log(self, req):
        """Handle AJAX log requests"""
        try:
            rev = int(req.args['logrev'])
            repos = self.env.get_repository()
            chgset = repos.get_changeset(rev)
            wikimsg = wiki_to_html(chgset.message, self.env, req, None, 
                                   True, False)
            data = {
                'chgset': True,
                'revision': rev,
                'time': format_datetime(chgset.date),
                'age': pretty_timedelta(chgset.date, None, 3600),
                'author': chgset.author or 'anonymous',
                'message': wikimsg, 
            }
            return 'revtree_log.html', {'log': data}, 'application/xhtml+xml'
        except Exception, e:
            raise TracError, "Invalid revision log request: %s" % e
        
    def _process_revtree(self, req):
        """Handle revtree generation requests"""
        tracrepos = self.env.get_repository()
        youngest = int(tracrepos.get_youngest_rev())
        oldest = max(self.oldest, int(tracrepos.get_oldest_rev()))
        if self.abstime:
            timebase = int(time.time())
        else:
            timebase = to_timestamp(tracrepos.get_changeset(youngest).date)
        revstore = RevtreeStore(self.env, req.authname, \
                                (oldest, youngest), 
                                timebase, self.style)
        if req.args.has_key('reset') and req.args['reset']:
            revstore.clear(req.session)
        else:
            revstore.load(req.session)
        if req.args:
            revstore.populate(req.args)
        revstore.compute_range(timebase)
        data = revstore.get_values()
                
        try:
            if not revstore.can_be_rendered():
                raise EmptyRangeError
            repos = Repository(self.env, req.authname)
            repos.build(self.bcre, revstore.revrange, revstore.timerange)
            (branches, authors) = \
                self._select_parameters(repos, req, revstore)
            svgrevtree = self.rt.get_revtree(repos, req)
            if revstore['branch']:
                sbranches = [revstore['branch']]
                sbranches.extend(filter(lambda t: t not in sbranches, 
                                        self.trunks))
            else:
                sbranches = None
            sauthors = revstore['author'] and [revstore['author']] or None
            if revstore['showdel']:
                hidetermbranch = False
            else:
                hidetermbranch = True
            svgrevtree.create(req, 
                              revisions=revstore.revrange, 
                              branches=sbranches, authors=sauthors, 
                              hidetermbranch=hidetermbranch, 
                              style=revstore['style'])
            svgrevtree.build()
            svgrevtree.render(self.scale*0.6)
            style = req.href.chrome('revtree/css/revtree.css')
            svgstyle = '<?xml-stylesheet href="%s" type="text/css"?>' % style
            data.update({
                'svg': Markup(unicode(str(svgrevtree), 'utf-8')),
                'svgstyle': Markup(svgstyle)
            })
            # create and order the drop-down list content, starting with the
            # global values 
            branches = repos.branches().keys()
            authors = repos.authors()
            # save the user parameters only if the tree can be rendered
            revstore.save(req.session)
        except EmptyRangeError:
            data.update({'errormsg': \
                         "Selected filters cannot render a revision tree"})
            # restore default parameters
            repos = Repository(self.env, req.authname)
            repos.build(self.bcre, revrange=(oldest, youngest))
            branches = repos.branches().keys()
            authors = repos.authors()
            
        revrange = repos.revision_range()
        revisions = self._get_ui_revisions((oldest, youngest), revrange)
        branches.sort()
        # prepend the trunks to the selected branches
        for b in filter(lambda t: t not in branches, self.trunks):
                branches.insert(0, b)
        branches = filter(None, branches)
        branches.insert(0, '')
        authors.sort()
        authors = filter(None, authors)
        authors.insert(0, '')

        dauthors = [dict(name=a, label=a or 'All') for a in authors]
        dbranches = [dict(name=b, label=b or 'All') for b in branches]
        
        data.update({
            'title': 'Revision Tree',
            'periods': self._get_periods(),
            'revmin': str(revrange[0]),
            'revmax': str(revrange[1]),
            'revisions': revisions,
            'branches': dbranches,
            'authors': dauthors
        })
                                                                               
        # add javascript for AJAX tooltips 
        add_script(req, 'revtree/js/svgtip.js')
        # add custom stylesheet
        add_stylesheet(req, 'revtree/css/revtree.css')
        return 'revtree.html', {'rt': data}, 'application/xhtml+xml'

    def _get_periods(self):
        """Generates a list of periods"""
        periods = RevtreeModule.PERIODS
        days = periods.keys()
        days.sort()
        return [dict(name=str(d), label=periods[d]) for d in days]

    def _get_ui_revisions(self, revspan, revrange):
        """Generates the list of displayable revisions"""
        (revmin, revmax) = revspan
        allrevisions = range(revmin, revmax+1)
        allrevisions.sort()
        revs = [c for c in allrevisions]
        revs.reverse()
        revisions = []
        for rev in revs:
            if len(revisions) > 50:
                if int(rev)%100 and (rev not in revrange):
                    continue
            elif len(revisions) > 30:
                if int(rev)%20 and (rev not in revrange):
                    continue
            elif len(revisions) > 10:
                if int(rev)%10 and (rev not in revrange):
                    continue
            revisions.append(str(rev))
        if revisions[-1] != str(revmin):
            revisions.append(str(revmin))
        return revisions

    def _select_parameters(self, repos, req, revstore):
        """Calculates the revisions/branches/authors to show as selectable
           properties for the revtree generation"""
        revs = [c for c in repos.changesets()]
        revs.reverse()
        brnames = [bn for bn in repos.branches().keys() \
                      if bn not in self.trunks]
        brnames.sort()
        branches = []
        authors = repos.authors()
        vbranches = None
        brfilter = revstore['branch']
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
        return (vbranches, authors)
