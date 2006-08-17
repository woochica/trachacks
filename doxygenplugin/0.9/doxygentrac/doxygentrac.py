# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
#

from __future__ import generators

import os
import time
import posixpath
import re
import mimetypes

from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.Search import ISearchSource
from trac.wiki import IWikiSyntaxProvider, wiki_to_html
from trac.wiki.formatter import system_message
from trac.util import Markup

def compare_rank(x, y):
    if x['rank'] == y['rank']:
        return 0
    elif x['rank'] > y['rank']:
        return -1
    return 1

class DoxygenPlugin(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler,
      ITemplateProvider, ISearchSource, IWikiSyntaxProvider)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['DOXYGEN_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'doxygen'
    def get_navigation_items(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            # Get config variables.
            title = self.env.config.get('doxygen', 'title', 'Doxygen')

            # Return mainnav buttons.
            yield 'mainnav', 'doxygen', Markup('<a href="%s">%s</a>' % \
              (self.env.href.doxygen() + '/', title))

    # IRequestHandler methods

    def match_request(self, req):
        # Get config variables.
        base_path = self.config.get('doxygen', 'path', '/var/lib/trac/doxygen')
        default_project = self.config.get('doxygen', 'default_project', '')
        ext = self.config.get('doxygen', 'ext', 'htm html png')
        ext = '|'.join(ext.split(' '))
        source_ext = self.config.get('doxygen', 'source_ext', 'idl odl java' \
          ' cs py php php4 inc phtml m cpp cxx c hpp hxx h')
        source_ext = '|'.join(source_ext.split(' '))

        # Match documentation request.
        self.log.debug(req.path_info)
        match = re.match('^/doxygen(?:/?$|/([^/]*)(?:/?$|/(.*)$))',
          req.path_info)
        if match:
            self.log.debug('matched group 1: %s' % (match.group(1),))
            self.log.debug('matched group 2: %s' % (match.group(2),))

            if not match.group(1) and not match.group(2):
                # Request for documentation index.
                req.args['path'] = os.path.join(base_path, default_project)
                req.args['action'] = 'index'
            else:
                # Get project and file from request.
                if not match.group(2):
                    project = default_project
                    file = match.group(1)
                else:
                    project = match.group(1)
                    file = match.group(2)

                self.log.debug('project: %s' % (project,))
                self.log.debug('file: %s' % (file,))

                if re.match(r'''^search.php$''', file):
                    # Request for searching.
                    req.args['action'] = 'search'

                elif re.match(r'''^(.*)[.](%s)''' % (ext,), file):
                    # Request for documentation file.
                    path = os.path.join(base_path, project, file)
                    self.log.debug('path: %s' % (path,))
                    if os.path.exists(path):
                        req.args['path'] = path
                        req.args['action'] = 'file'
                    else:
                        req.args['action'] = 'search'
                        req.args['query'] = file

                else:
                    match = re.match(r'''^(.*)[.](%s)''' % (source_ext,), file)
                    if match:
                        # Request for source file documentation.
                        path = os.path.join(base_path, project, '%s_8%s.html'
                          % (match.group(1), match.group(2)))
                        self.log.debug('path: %s' % (path,))
                        if os.path.exists(path):
                            req.args['path'] = path
                            req.args['action'] = 'file'
                        else:
                            req.args['action'] = 'search'
                            req.args['query'] = file

                    else:
                        path = os.path.join(base_path, project, 'class%s.html'
                          % (file,))
                        if os.path.exists(path):
                            req.args['path'] = path
                            req.args['action'] = 'file'
                        else:
                            path = os.path.join(base_path, project,
                              'struct%s.html' % (file,))
                            if os.path.exists(path):
                                req.args['path'] = path
                                req.args['action'] = 'file'
                            else:
                                results = self._search_in_project(project,
                                  [file])
                                for result in results:
                                    self.log.debug(result)
                                    if result['name'] == file:
                                        req.redirect(self.env.href.doxygen(
                                          project) + '/' + result['url'])
                                req.args['action'] = 'search'
                                req.args['query'] = file

            # Request matched.
            return True

        else:
            # Request not matched.
            return False

    def process_request(self, req):
        req.perm.assert_permission('DOXYGEN_VIEW')

        # Get request arguments
        path = req.args.get('path')
        action = req.args.get('action')

        # Get config variables
        index =  self.config.get('doxygen', 'index', 'main.html')
        wiki_index = self.config.get('doxygen', 'wiki_index', None)

        # Redirect search requests.
        if action == 'search':
            req.redirect('%s?q=%s&doxygen=on' % (self.env.href.search(),
              req.args.get('query')))

        # Retrun apropriate content to type or search request
        elif action == 'index':
            if wiki_index:
                # Get access to database
                db = self.env.get_db_cnx()
                cursor = db.cursor()

                # Get wiki index
                sql = "SELECT text FROM wiki WHERE name = %s"
                cursor.execute(sql, (wiki_index,))
                text = Markup(system_message('Error', 'Wiki page %s does not' \
                  ' exists' % (wiki_index)))
                for row in cursor:
                    text = wiki_to_html(row[0], self.env, req)

                # Display wiki index page
                req.hdf['doxygen.text'] = text
                return 'doxygen.cs', 'text/html'
            else:
                add_stylesheet(req, 'doxygen/css/doxygen.css')
                req.hdf['doxygen.path'] = path + '/' + index
                return 'doxygen.cs', 'text/html'

        elif action == 'file':
            type = mimetypes.guess_type(path)[0]

            if type == 'text/html':
                add_stylesheet(req, 'doxygen/css/doxygen.css')
                req.hdf['doxygen.path'] = path
                return 'doxygen.cs', 'text/html'
            else:
                req.send_file(path, type)

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('doxygen', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ISearchProvider methods

    def get_search_filters(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            # Get config variables
            title = self.env.config.get('doxygen', 'title', 'Doxygen')

            yield('doxygen', title)

    def get_search_results(self, req, query, filters):
        if not 'doxygen' in filters:
            return
        if query[0] == query[-1] == "'" or query[0] == query[-1] == '"':
            keywords = [query[1:-1]]
        else:
            keywords = query.split(' ')

        base_path = self.config.get('doxygen', 'path')

        for project in os.listdir(base_path):
            # Search in project documentation directories
            path = os.path.join(base_path, project)
            if os.path.isdir(path):
                index = os.path.join(path, 'search.idx')
                if os.path.exists(index):
                    creation = os.path.getctime(index)
                    for result in  self._search_in_project(project, keywords):
                        result['url'] =  self.env.href.doxygen(project) + '/' \
                          + result['url']
                        yield result['url'], result['name'], creation, \
                          'doxygen', None

            # Search in common documentation directory
            index = os.path.join(base_path, 'search.idx')
            if os.path.exists(index):
                creation = os.path.getctime(index)
                for result in self._search_in_project('', keywords):
                    result['url'] =  self.env.href.doxygen() + '/' + \
                      result['url']
                    yield result['url'], result['name'], creation, 'doxygen', \
                      None

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('doxygen', self._doxygen_link)

    def get_wiki_syntax(self):
        return []

    # internal methods
    def _search_in_project(self, project, keywords):
        # Open index file for project documentation
        base_path = self.config.get('doxygen', 'path')
        index = os.path.join(base_path, project, 'search.idx')
        if os.path.exists(index):
            fd = open(index)

            # Search for keywords in index
            results = []
            for keyword in keywords:
                results += self._search(fd, keyword)
                results.sort(compare_rank)
                for result in results:
                    yield result

    def _search(self, fd, word):
        results = []
        index = self._computeIndex(word)
        if index != -1:
            fd.seek(index * 4 + 4, 0)
            index = self._readInt(fd)

            if index:
                fd.seek(index)
                w = self._readString(fd)
                matches = []
                while w != "":
                    statIdx = self._readInt(fd)
                    low = word.lower()
                    if w.find(low) != -1:
                        matches.append({'word' : word, 'match' : w, 'index' : statIdx, 'full' : len(low) == len(w)})
                    w = self._readString(fd)

                count = 0
                totalHi = 0
                totalFreqHi = 0
                totalFreqLo = 0

                for match in matches:
                    multiplier = 1
                    if match['full']:
                        multiplier = 2

                    fd.seek(match['index'])
                    numDocs = self._readInt(fd)

                    for i in range(numDocs):
                        idx = self._readInt(fd)
                        freq = self._readInt(fd)
                        results.append({'idx' : idx, 'freq' : freq >> 1, 'hi' : freq & 1, 'multi' : multiplier})
                        if freq & 1:
                            totalHi += 1
                            totalFreqHi += freq * multiplier
                        else:
                            totalFreqLo += freq * multiplier

                    for i in range(numDocs):
                        fd.seek(results[count]['idx'])
                        name = self._readString(fd)
                        url = self._readString(fd)
                        results[count]['name'] = name
                        results[count]['url'] = url
                        count += 1

                totalFreq = (totalHi + 1) * totalFreqLo + totalFreqHi
                for i in range(count):
                    freq = results[i]['freq']
                    multi = results[i]['multi']
                    if results[i]['hi']:
                        results[i]['rank'] = float((freq * multi + totalFreqLo)) / float(totalFreq)
                    else:
                        results[i]['rank'] = float((freq * multi)) / float(totalFreq)

        return results

    def _computeIndex(self, word):
        if len(word) < 2:
            return -1

        hi = ord(word[0].lower())
        if hi == 0:
            return -1

        lo = ord(word[1].lower())
        if lo == 0:
            return -1

        return hi * 256 + lo

    def _readInt(self, fd):
        b1 = fd.read(1)
        b2 = fd.read(1)
        b3 = fd.read(1)
        b4 = fd.read(1)

        return (ord(b1) << 24) | (ord(b2) << 16) | (ord(b3) << 8) | ord(b4)

    def _readString(self, fd):
        result = ''
        byte = fd.read(1)
        while byte != '\0':
            result = ''.join([result, byte])
            byte = fd.read(1)
        return result

    def _doxygen_link(self, formatter, ns, params, label):
        if ns == 'doxygen':
            return '<a href="%s" title="%s">%s</a>' % \
              (self.env.href.doxygen(params), params, label)
        else:
            return '<a href="%s" class="missing">%s?</a>' % \
              (self.env.href.doxygen(), label)
