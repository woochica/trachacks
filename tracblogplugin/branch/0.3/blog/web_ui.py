# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 John Hampton <pacopablo@asylumware.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at:
# http://trac-hacks.org/wiki/TracBlogPlugin
#
# Author: John Hampton <pacopablo@asylumware.com>

import sys
import time
import datetime
import inspect
import calendar
import re
from StringIO import StringIO
from pkg_resources import resource_filename
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_link
from trac.web.chrome import INavigationContributor 
from trac.util import Markup, format_date, format_datetime, unicode_urlencode
from trac.wiki.formatter import Formatter, wiki_to_oneliner
from trac.wiki.model import WikiPage
from trac.wiki.api import IWikiMacroProvider
from trac.perm import IPermissionRequestor

from tractags.api import TagEngine
from tractags.parseargs import parseargs

from tBlog.util import bool_val, list_val

__all__ = ['TracBlogPlugin']

blog_params = {
        'macro_blacklist' : {'req'     : None,
                             'kwargs'  : None,
                             'default' : [],
                             'convert' : list_val, }, 
        'mark_updated'    : {'default' : True,
                             'convert' : bool_val, }, 
        'num_posts'       : {'config'  : None,
                             'convert' : int, }, 
        'date_format'     : {'req'     : None,
                             'kwargs'  : None,
                             'default' : '%x %X', }, 
        'read_post'       : {'req'     : None,
                             'kwargs'  : None,
                             'default' : '[wiki:%s Read Post]', },
       }

def get_env_val(key, req=None, kwargs=None, config=None, section=None, 
                default=None, convert=None):
    """Return the value for the specified key from the complete environment

    Value retrieval follows the following pattern:
     * Check the request object and return value if present
     * Check the kwargs object and return value if present
     * Check the config file and return value if present
     * If a default value is specified, return that, else return None

    A conversion function can be specified.  If present, the value will be
    passed to the conversion function before returning.  If the conversion
    function raises an error, None will be returned.

    """
    val = None
    if req:
        val = req.args.getlist(key)
        if len(val) == 1:
            val = val[0]
    if (not val and not isinstance(val, bool)) and kwargs:
        if kwargs.has_key(key):
           val = kwargs[key]
    if (not val and not isinstance(val, bool)) and config and section:
        val = config.get(section, key)
    if not val and not isinstance(val, bool):
        val = default
    if val and convert:
        try:
            val = convert(val)
        except:
            val = None
    return val

class NoFloatFormatter(Formatter):
    """A modified formatter that inserts macro_no_float=1 into the HDF."""
    
    def __init__(self, *args, **kwords):
        if 'macro_blacklist' in kwords:
            self.macro_blacklist = kwords['macro_blacklist']
            del kwords['macro_blacklist']
        if 'req' in kwords:
            kwords['req'].hdf['macro_no_float'] = 1
        else:
            for arg in args:
                if hasattr(arg, 'hdf'):
                    arg.hdf['macro_no_float'] = 1
                    break
            else:
                raise TracError, "Unable to isolate req"
        super(NoFloatFormatter,self).__init__(*args, **kwords)

    def _macro_formatter(self, match, fullmatch):
        name = fullmatch.group('macroname')
        if name in self.macro_blacklist:
            return ''
        return super(NoFloatFormatter, self)._macro_formatter(match, fullmatch)
        
def wiki_to_nofloat_html(wikitext, env, req, db=None, absurls=0, 
                         escape_newlines=False, macro_blacklist=[]):
    out = StringIO()
    NoFloatFormatter(env, req, absurls, db, macro_blacklist=macro_blacklist
                    ).format(wikitext, out, escape_newlines)
    return Markup(out.getvalue())

class TracBlogPlugin(Component):
    """Displays a blog based on tags
    
    The list of tags to be shown can be specified as arguments to the macro.
    If no tags are specified as parameters, then the default 'blog' tag is
    used.

    The following options can be specified:

    '''union''' - Specify whether the join for the tags listed should be a
    union or intersection(default).[[br]]
    '''num_posts''' - Number of posts to display.[[br]]
    '''year''' - Year for which to show posts.[[br]]
    '''month''' - Month for which to show posts.[[br]]
    '''day''' - Day of the month for which to show posts.[[br]]
    '''delta''' - How many days of posts should be shown.[[br]]
    '''mark_update''' - Specify whether to show "Updated on" for posts that
    have been updated.[[br]]

    If specifying dates with {{{year}}}, {{{month}}}, and/or {{{day}}}, the
    current value is specified if missing.  For example, if {{{day}}} is 
    specified but {{{year}}} and {{{month}}} are not, then {{{year}}} will be
    filled in with the current year and {{{month}}} will be filled with the 
    current month.  If only {{{year}}} and {{{month}}} are specified, then that
    indicates the whole month is desired.

    The {{{num_posts}}} options is bounded by the date options if combined. For
    example, if {{{num_posts=5}}} and {{{month=4}}} is specified, it will show 
    up to 5 posts from the month of April.  If only 3 posts exist, then only 3 
    are shown.  If a date option is not specified, then it will show the last 
    {{{num_posts}}} posts.

    === Examples ===
    {{{
    [[BlogShow()]]
    [[BlogShow(blog,pacopablo)]]
    [[BlogShow(blog,pacopablo,union=True)]]
    [[BlogShow(blog,pacopablo,num_posts=5)]]
    [[BlogShow(blog,pacopablo,month=4,num_posts=5)]]
    [[BlogShow(blog,pacopablo,year=2006,month=4)]]
    [[BlogShow(blog,pacopablo,year=2006,month=4,day=12)]]
    [[BlogShow(blog,pacopablo,delta=5)]]
    [[BlogShow(blog,pacopablo,delta=5,mark_updated=False)]]
    }}}
    """

    implements(IRequestHandler, ITemplateProvider, INavigationContributor,
               IWikiMacroProvider, IPermissionRequestor)

    # IPermissionRequestor
    def get_permission_actions(self):
        yield 'BLOG_VIEW'

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if req.perm.has_permission('BLOG_VIEW'):
            return 'blog'
                
    def get_navigation_items(self, req):
        nav_bar = bool_val(self.env.config.get('blog', 'nav_bar', True))
        if req.perm.has_permission('BLOG_VIEW') and nav_bar:
            req.hdf['trac.href.blog'] = self.env.href.blog()
            lname = get_env_val('nav_link', config=self.env.config,
                                section='blog', default='Blog')
            yield 'mainnav', 'blog', Markup('<a href="%s">%s</a>',
                                             self.env.href.blog(), lname)

    # IWikiMacroProvider
    def get_macros(self):
        yield 'BlogShow'

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        """ Display the blog in the wiki page """
        add_stylesheet(req, 'blog/css/blog.css')
        tags, kwargs = self._get_params(content=content)
        rss_href = self.env.href.blog(format='rss', tag=tags, **kwargs)
        add_link(req, 'alternate', rss_href, 'Blog RSS Feed', 
                'application/rss+xml', 'rss')
        self._generate_blog(req, tags, kwargs)
        req.hdf['blog.macro'] = True
        data = req.hdf.render('blog.cs')
        return unicode(req.hdf.render('blog.cs'), 'utf-8')

    # IRequestHandler
    def match_request(self, req):
        return req.path_info == '/blog'

    def process_request(self, req):
        req.perm.assert_permission('BLOG_VIEW')
        add_stylesheet(req, 'blog/css/blog.css')
        add_stylesheet(req, 'common/css/wiki.css')
        tags, kwargs = self._get_params(req=req)
        rss_href = self.env.href.blog(format='rss', tag=tags, **kwargs)
        add_link(req, 'alternate', rss_href, 'Blog RSS Feed', 
                'application/rss+xml', 'rss')
        self._generate_blog(req, tags, kwargs)
        return 'blog.cs', None

    def _get_params(self, req=None, content=None):
        tags = []
        kwargs = {}
        if content:
            tags, kwargs = parseargs(content)
        elif req:
            tags = get_env_val('tag', req)
            kwargs = {}
            for key in req.args.keys():
                if key != 'tag':
                    kwargs[key] = req.args[key]
                continue
        if not tags:
            tags = get_env_val('default_tag', config=self.env.config,
                                section='blog', default='blog', convert=list_val)
        return tags, kwargs

    def _get_display_params(self, req, kwargs):
        """ Extract the optional display parameters

        Return a dictionary with the values and stuff

        """
        global blog_params
        parms = { 'req'     : req,
                  'kwargs'  : kwargs,
                  'config'  : self.env.config,
                  'section' : 'blog',
                  'default' : None,
                  'convert' : None,
                }
        vals = {}
        for k, v in blog_params.items():
            p = {}
            p.update(parms)
            for pk, pv in v.items():
                p[pk] = pv    
            vals[k] = get_env_val(k, **p)
            continue
        return vals

    def _generate_blog(self, req, args, kwargs):
        """Extract the blog pages and fill the HDF.

        *args is a list of tags to use to limit the blog scope
        **kwargs are any aditional keyword arguments that are needed
        """
        tallies = {}
        blog, tlist, tags = self._initialize_tags(req, *args, **kwargs)
        poststart, postend, default_times = self._get_time_range(req, **kwargs)
        parms = self._get_display_params(req, kwargs)

        # Formatting
        entries = {}
        if parms['num_posts'] and default_times:
            poststart = sys.maxint
            postend = 0

        for blog_entry in blog:
            page = WikiPage(self.env, version=1, name=blog_entry)
            version, post_time, author, comment, ipnr = page.get_history(
                                                        ).next()
            self._add_to_tallies(tallies, post_time, blog_entry)
            page = WikiPage(self.env, name=blog_entry)
            version, modified, author, comment, ipnr = page.get_history(
                                                       ).next()
            if poststart >= post_time >= postend:       
                timeStr = format_datetime(post_time, 
                                          format=parms['date_format']) 
                text = self._trim_page(page.text, blog_entry)
                pagetags = [x for x in tags.get_name_tags(blog_entry) 
                            if x not in tlist]
                tagtags = []
                for i, t in enumerate(pagetags[:3]):
                    d = { 'link' : t,
                          'name' : t,
                          'last' : i == 2,
                        }
                    tagtags.append(d)
                    continue
                data = {
                        'name'      : blog_entry,
                        'wiki_link' : wiki_to_oneliner(parms['read_post'] % 
                                                       blog_entry,
                                                       self.env),
                        'time'      : timeStr,
                        'author'    : author,
                        'wiki_text' : wiki_to_nofloat_html(text, self.env, req,
                                      macro_blacklist=parms['macro_blacklist']),
                        'comment'   : wiki_to_oneliner(comment, self.env),
                        'tags'      : {
                                        'present' : len(pagetags),
                                        'tags'    : tagtags,
                                        'more'    : len(pagetags) > 3 or 0,
                                      },
                       }
                if (modified != post_time) and parms['mark_updated']:
                    data['modified'] = 1
                    mod_str = format_datetime(modified, 
                                              format=parms['date_format'])
                    data['mod_time'] = mod_str
                entries[post_time] = data
            continue
        tlist = entries.keys()
        tlist.sort()
        tlist.reverse()
        if parms['num_posts'] and (parms['num_posts'] <= len(tlist)):
            tlist = tlist[:parms['num_posts']]
        if tlist:
            entries[tlist[-1]]['last'] = 1
        req.hdf['blog.entries'] = [entries[x] for x in tlist]
        bloglink = self.env.config.get('blog', 'new_blog_link', 'New Blog Post')
        req.hdf['blog.newblog'] = bloglink
        hidecal = self._choose_value('hidecal', req, kwargs)
        if not hidecal:
            self._generate_calendar(req, tallies)
        req.hdf['blog.hidecal'] = hidecal
        pass

    def _initialize_tags(self, req, *args, **kwargs):
        """ Instantiate a TagEngine and get the tagged names

        Returns a list of all the pages tagged with the tags specified in
        *args.  Also return a reference to the TagEngine instance

        """
        tags = TagEngine(self.env).tagspace.wiki
        union = False
        if kwargs.has_key('union'):
            union = kwargs['union']

        tlist = args
        if not len(tlist):
            tlist = [self.env.config.get('blog', 'default_tag', 'blog')]
            self.log.debug('tlist: %s' % str(tlist))

        if union:
            blog = tags.get_tagged_names(tlist, operation='union')
        else:
            blog = tags.get_tagged_names(tlist, operation='intersection')
        return (blog, tlist, tags)
    

    def _generate_calendar(self, req, tallies):
        """Generate data necessary for the calendar

        """
        now = datetime.datetime.now()
        year = self._choose_value('year', req, None, convert=int) or \
               now.year
        month = self._choose_value('month', req, None, convert=int) or \
                now.month
        day = self._choose_value('day', req, None, convert=int) or \
              now.day 
        baseday = datetime.datetime(year, month, day)
        week_day = self.env.config.get('blog', 'first_week_day', 'SUNDAY')
        first_day = getattr(calendar, week_day.upper())
        calendar.setfirstweekday(first_day)
        cal = calendar.monthcalendar(year, month)
        statcal = {}
        for week_num, week in enumerate(cal):
            statcal[week_num] = {
                                'num' : week_num,
                                'days' : []
                               }
            for day_num in week:
                d = { 'num' : day_num,
                      'count' : 0, }
                if day_num:
                    d['count'] = self._get_tally(tallies, year, month, day_num)
                statcal[week_num]['days'].append(d)
                continue
            continue
        week = [week for week in xrange(len(cal)) if day in cal[week]][0]
        monthname = format_datetime(time.mktime(baseday.timetuple()), 
                                    format="%b") 
        lastyear = abs(year - 1)
        nextyear = year + 1
        # for the prev/next navigation links
        lastmonth = month - 1
        lastmonth_year = year
        nextmonth = month + 1
        nextmonth_year = year
        # check for year change (KISS version)
        if lastmonth <= 0:
            lastmonth = 12
            lastmonth_year -= 1
        if nextmonth >= 13:
            nextmonth = 1
            nextmonth_year += 1

        hdfdate = {
                    'year' : year,
                    'yearcount' : self._get_tally(tallies, year),
                    'month' : month, 
                    'monthcount' : self._get_tally(tallies, year, month),
                    'day' : day,
                    'lastyear' : lastyear,
                    'nextyear' : nextyear,
                    'lastmonth' : {
                                    'year' : lastmonth_year,
                                    'month' : lastmonth,
                                  },
                    'nextmonth' : {
                                    'year' : nextmonth_year,
                                    'month' : nextmonth,
                                  },
                    'daynames' : calendar.weekheader(2).split(),
                    'week' : week,
                    'monthname' : monthname,
                  }
        req.hdf['blog.date'] = hdfdate
        req.hdf['blog.cal'] = statcal
        req.hdf['blog.path_info'] = self.env.href(req.path_info)
        pass

    def _get_tally(self, tallies, year, month=None, day=None):
        """Return the tally for the given date

        Returns 0 if no tally is present

        """
        if day and month:
            try:    
                tally = tallies[year][month][day]['total']
            except KeyError:
                tally = 0
        elif month:
            try:    
                tally = tallies[year][month]['total']
            except KeyError:
                tally = 0
        else:
            try:    
                tally = tallies[year]['total']
            except KeyError:
                tally = 0
        return tally

    def _add_to_tallies(self, tallies,  post_time, page_name):
        """Create a running tally of blog page data

        """
        def _gen_blank_year_total(year):
            blank_year = {}
            for month in xrange(1, 13):
                mrange = calendar.monthrange(year, month)[1] 
                blank_year[month] = { 'pages' : [],
                                      'total' : 0, }
                for day in xrange(1, mrange + 1):
                    blank_year[month][day] = { 'total' : 0,
                                               'pages' : [], }
                    continue
                continue
            return blank_year
        d = datetime.datetime.fromtimestamp(post_time)
        try:
            tallies['total'] += 1
        except KeyError:
            tallies['total'] = 1
        try:
            tallies[d.year]['total'] += 1
            tallies[d.year]['pages'].append(page_name)
        except (KeyError, AttributeError):
            tallies[d.year] = _gen_blank_year_total(d.year)
            tallies[d.year]['total'] = 1
            tallies[d.year]['pages'] = [page_name]
        tallies[d.year][d.month]['total'] += 1
        tallies[d.year][d.month]['pages'].append(page_name)
        tallies[d.year][d.month][d.day]['total'] += 1
        tallies[d.year][d.month][d.day]['pages'].append(page_name)
        pass

    def _get_time_range(self, req, **kwargs):
        """Return a start and end date range

        Parameters can be passed in via the req object or via **kwargs.  
        The req object always overrides **kwargs.  In practice, this shouldn't
        matter much as the macro will use **kwargs and the nav item will use
        req.  Just documenting behavior.

        The range of days can be specified in multiple ways.
        * Specify date range with startdate and enddate.  Value should be 
          seconds since epoch
        * Specify startdate and delta. delta should be a number of seconds. If
          both enddate and delta are specified, enddate is preferred.
        * Specify any combination of year, month, day.  If any one of the
          values is specified, then it will use this method in place of 
          startdate, enddate and delta.  If a value is missing that is required
          such as a year if month is specified, then it deafults to the current
          value.  Otherwise it generates a range according to the values passed
          in.  For example, year=2006 and month=12 will return all posts for 
          December 2006.

        """
        DAY = 86400
        HISTORY = int(self.env.config.get('blog', 'history_days') or 30) * DAY

        startdate = self._choose_value('startdate', req, kwargs, convert=int)
        enddate = self._choose_value('enddate', req, kwargs, convert=int)
        delta = self._choose_value('delta', req, kwargs, convert=int)
        year = self._choose_value('year', req, kwargs, convert=int)
        month = self._choose_value('month', req, kwargs, convert=int)
        day = self._choose_value('day', req, kwargs, convert=int)
        defaults = not (startdate or enddate or delta or year or month or day)
        now = datetime.datetime.now()
        oneday = datetime.timedelta(days=1)
        if year or month or day:
            if day:
                year = year or now.year
                month = month or now.month
            if month:
                year = year or now.year
            days_in_month = calendar.monthrange(year, month or 12)[1]
            start = datetime.datetime(year, month or 12, 
                                      day or days_in_month)
            start += oneday
            end = datetime.datetime(year, month or 1, day or 1)
            start = time.mktime(start.timetuple())
            end = time.mktime(end.timetuple())
        else:
            start = startdate or time.mktime(now.timetuple())
            if enddate:
                end = enddate
            elif delta:
                end = start - delta
            else:
                end = start - HISTORY
        return start, end, defaults

    def _choose_value(self, key, req, kwargs, convert=None):
        """Return the value for the specified key from either req or kwargs

        If the value is present in both, then the value from req is used.
        If the value doesn't exist in either, then None is returned.

        An optional conversion function can be passed.  If present, the value
        will be passed to the conversion function before returning.  If the
        conversion function raises an error, None will be returned

        I need a little more from this.

         * Check req
         * Check kwargs
         * Check trac.ini
         * Use default or return None

        """
        val = req.args.get(key, None)
        if not val:
            try:
                val = kwargs[key]
            except:
                val = None
        if convert:
            try:
                val = convert(val)
            except:
                val = None
        return val

    def _trim_page(self, text, page_name):
        """Trim the page text to the {{{post_size}} in trac.ini

        The timming isn't exact.  It trims to the first line that causes the
        page to exceed the value storing in {{{post_size}}}.  If the line is
        in the middle of a code block, it will close the block.

        """
        post_size = int(self.env.config.get('blog', 'post_size', 1024))
        tlines = []
        entry_size = 0
        line_count = 0
        in_code_block = False
        lines = text.split('\n')
        for line in lines:
            line_count += 1
            entry_size += len(line)
            tlines.append(line)
            if not in_code_block:
                in_code_block = line.strip() == '{{{'
            else:
                in_code_block = in_code_block and line.strip() != '}}}'
            if entry_size > post_size:
                if in_code_block:
                    tlines.append('}}}')
                break
            continue
        if line_count < len(lines):
            tlines.append("''[wiki:%s (...)]''" % page_name)
            
        return '\n'.join(tlines)

    # ITemplateProvider
    def get_templates_dirs(self):
        """ Return the absolute path of the directory containing the provided
            templates

        """
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """ Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.

        """
        return [('blog', resource_filename(__name__, 'htdocs'))]


