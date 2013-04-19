# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import calendar
import datetime
import feedparser
import os
import sys
import urllib2

from genshi.builder import tag
from trac.core import *
from trac.env import open_environment
from trac.web.api import IRequestHandler
from trac.web.chrome import add_ctxtnav
from trac.web.href import Href
from trachours.api import hours_format
from trachours.feed import total_hours
from trachours.utils import get_date
from trachours.utils import urljoin

try:
    import lxml.html
    def projects_from_url(url):
        """returns list of projects from the index url"""
        projects = [] # XXX should be a set?
        html = urllib2.urlopen(url).read()
        html = lxml.html.fromstring(html)
        for link in html.iterlinks():
            projects.append(link[2].strip('/'))
        return projects
except ImportError:
    pass

def projects_from_directory(directory):
    """returns list of projects from a directory"""
    projects = []
    for entry in os.listdir(directory):
        try:
            open_environment(os.path.join(directory, entry))
        except:
            continue
        projects.append(entry)
    return projects

def query_all(projects, path, base_url=None):
    """
    * projects: urls
    * path: 
    """
    feeds = {}
    for project in projects:
        if base_url:
            url = urljoin(base_url, project, path)
        else:
            url = urljoin(project, path) 
        
        feed = feedparser.parse(url)
        if hasattr(feed.feed, 'title'):
            feeds[project] = feed
        else:
            feeds[project] = None
    return feeds

def query_from_url(url, path='/hours?format=rss', directory=None):
    if directory:
        proj = projects_from_directory(directory)
    else:
        proj = projects_from_url(url)
    feeds = query_all(proj, path, base_url=url)

    project_hours = {}
    projects = set()
    for project, feed in feeds.items():
        if feed is not None:
            hours = total_hours(feed)
            for worker in hours:
                project_hours.setdefault(worker, {})[project] = hours[worker]
            projects.add(project)

    projects = sorted(projects)
    rows = [ ]
    rows.append(['worker'] + projects + ['total'])
    for worker in sorted(project_hours):
        row = [ worker ]
        total = 0.;
        for project in projects:
            value = project_hours[worker].get(project, 0.)
            row.append(value)
            total += value
        row.append(total)
        rows.append(row)
    return rows

class MultiprojectHours(Component):

    implements(IRequestHandler)

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.rstrip('/') == '/hours/multiproject'

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """
        data = {}
        now = datetime.datetime.now()

        # XXX copy + pasted from hours.py
        data['months'] = [ (i, calendar.month_name[i]) for i in range(1,13) ]        
        data['years'] = range(now.year, now.year - 10, -1)
        data['days'] = range(1, 32)        

        # get the date range for the query
        if 'from_year' in req.args:
            from_date = get_date(req.args['from_year'], 
                                 req.args.get('from_month'),
                                 req.args.get('from_day'))

        else:
            from_date = datetime.datetime(now.year, now.month, now.day)
            from_date = from_date - datetime.timedelta(days=7) # 1 week ago, by default

        if 'to_year' in req.args:
            to_date = get_date(req.args['to_year'], 
                                 req.args.get('to_month'),
                                 req.args.get('to_day'),
                                 end_of_day=True)
        else:
            to_date = now

        data['from_date'] = from_date
        data['to_date'] = to_date

        # get the data from the projects
        url = req.abs_href().rstrip('/').rsplit('/', 1)[0] # url for all projects
        for string in 'from', 'to':
            for field in 'year', 'month', 'day':
                req.args['%s_%s' % (string, field)] = getattr(data['%s_date' % string], field)
        kw = req.args.copy()
        kw['format'] = 'rss'
        path = Href('/hours')(**kw)

        # directory for all projects
        # XXX this could be configurable in an intelligent way
        directory = os.path.split(self.env.path)[0] 

        rows = query_from_url(url, path=path, directory=directory)
        data['rows'] = rows[1:] 
        data['projects'] = []

        # make some nice links from the data
        project_urls = []
        for project in rows[0][1:-1]:
            data['projects'].append(project)
            url = Href('/%s' % project)('hours', **req.args)
            project_urls.append(tag.a(project, href=url))
        rows[0][1:-1] = project_urls

        data['headers'] = rows[0]

        total = 0.
        for row in data['rows']:
            worker = row[0]
            kw = req.args.copy()
            kw['worker'] = worker
            url = req.href(req.path_info, **kw)
            row[0] = tag.a(worker, href=url, title="Cross-project hours for %s" % worker)
            project_urls = []
            for index, project in enumerate(data['projects']):
                kw = req.args.copy()
                kw['worker_filter'] = worker
                url = Href('/%s' % project)('hours', **kw)
                hours = hours_format % row[index+1]
                project_urls.append(tag.a(hours, href=url, title="Hours for %s on %s" % (worker, project)))
            row[1:-1] = project_urls
            total += row[-1]
            row[-1] = hours_format % row[-1]

        data['total'] = hours_format % total
            
        return ('hours_multiproject.html', data, 'text/html')


if __name__ == '__main__':
    from optparse import OptionParser
    from pprint import pprint
    parser = OptionParser()
    options, args = parser.parse_args()
    for url in args:
        rows = query_from_url(url)
        print '%s:' % url
        pprint(rows)
