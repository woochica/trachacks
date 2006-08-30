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

from trac.config import Option
from trac.core import *
from trac.web import IRequestHandler
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
  add_stylesheet
from trac.Search import ISearchSource
from trac.wiki import IWikiSyntaxProvider, wiki_to_html
from trac.wiki.formatter import system_message
from trac.util.html import html

def compare_rank(x, y):
    if x['rank'] == y['rank']:
        return 0
    elif x['rank'] > y['rank']:
        return -1
    return 1

class DoxygenPlugin(Component):
    implements(IPermissionRequestor, INavigationContributor, IRequestHandler,
      ITemplateProvider, ISearchSource, IWikiSyntaxProvider)

    base_path = Option('doxygen', 'path', '/var/lib/trac/doxygen',
      """Directory containing doxygen generated files.""")

    default_doc = Option('doxygen', 'default_documentation', '',
      """Default path relative to `base_path` in which to look for
      documentation files.""")

    title = Option('doxygen', 'title', 'Doxygen',
      """Title to use for the main navigation tab.""")

    ext = Option('doxygen', 'ext', 'htm html png',
      """Space separated list of extensions for doxygen managed files.""")

    source_ext = Option('doxygen', 'source_ext',
      'idl odl java cs py php php4 inc phtml m '
      'cpp cxx c hpp hxx h',
      """Space separated list of source files extensions""")

    index = Option('doxygen', 'index', 'main.html',
      """Default index page to pick in the generated documentation.""")

    wiki_index = Option('doxygen', 'wiki_index', None,
      """Wiki page to use as the default page for the Doxygen main page.""")

    encoding = Option('doxygen', 'encoding', 'iso-8859-1',
      """Default encoding used by the generated documentation files.""")

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['DOXYGEN_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'doxygen'

    def get_navigation_items(self, req):
        if req.perm.has_permission('DOXYGEN_VIEW'):
            # Return mainnav buttons.
            yield 'mainnav', 'doxygen', html.a(self.title,
              href = req.href.doxygen())

    # IRequestHandler methods

    def match_request(self, req):
        ext = '|'.join(self.ext.split(' '))
        source_ext = '|'.join(self.source_ext.split(' '))

        # Match documentation request.
        self.log.debug(req.path_info)
        match = re.match('^/doxygen(?:/?$|/([^/]*)(?:/?$|/(.*)$))',
          req.path_info)
        if match:
            self.log.debug('matched group 1: %s' % (match.group(1),))
            self.log.debug('matched group 2: %s' % (match.group(2),))

            if not match.group(1) and not match.group(2):
                # Request for documentation index.
                req.args['path'] = os.path.join(self.base_path,
                  self.default_doc)
                req.args['action'] = 'index'
            else:
                # Get doc and file from request.
                if not match.group(2):
                    doc = self.default_doc
                    file = match.group(1)
                else:
                    doc = match.group(1)
                    file = match.group(2)

                self.log.debug('documentation: %s' % (doc,))
                self.log.debug('file: %s' % (file,))

                if re.match(r'''^search.php$''', file):
                    # Request for searching.
                    req.args['action'] = 'search'

                elif re.match(r'''^(.*)[.](%s)''' % (ext,), file):
                    # Request for documentation file.
                    path = os.path.join(self.base_path, doc, file)
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
                        path = os.path.join(self.base_path, doc, '%s_8%s.html'
                          % (match.group(1), match.group(2)))
                        self.log.debug('path: %s' % (path,))
                        if os.path.exists(path):
                            req.args['path'] = path
                            req.args['action'] = 'file'
                        else:
                            req.args['action'] = 'search'
                            req.args['query'] = file

                    else:
                        path = os.path.join(self.base_path, doc, 'class%s.html'
                          % (file,))
                        if os.path.exists(path):
                            req.args['path'] = path
                            req.args['action'] = 'file'
                        else:
                            path = os.path.join(self.base_path, doc,
                              'struct%s.html' % (file,))
                            if os.path.exists(path):
                                req.args['path'] = path
                                req.args['action'] = 'file'
                            else:
                                results = self._search_in_documentation(doc,
                                  [file])
                                for result in results:
                                    self.log.debug(result)
                                    if result['name'] == file:
                                        req.redirect(req.href.doxygen(doc)
                                          + '/' + result['url'])
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

        self.log.debug('path: %s' % (path,))
        self.log.debug('action: %s' % (action,))

        # Redirect search requests.
        if action == 'search':
            req.redirect(req.href.search(q = req.args.get('query'),
              doxygen = 'on'))

        # Retrun apropriate content to type or search request
        elif action == 'index':
            if self.wiki_index:
                # Get access to database
                db = self.env.get_db_cnx()
                cursor = db.cursor()

                # Get wiki index  # FIXME: use WikiPage() instead
                sql = "SELECT text FROM wiki WHERE name = %s"
                cursor.execute(sql, (self.wiki_index,))
                text = system_message('Error', 'Wiki page %s does not exists' %
                  self.wiki_index)
                for row in cursor:
                    text = wiki_to_html(row[0], self.env, req)

                # Display wiki index page
                req.hdf['doxygen.text'] = text
                return 'doxygen.cs', 'text/html'
            else:
                add_stylesheet(req, 'doxygen/css/doxygen.css')
                req.hdf['doxygen.path'] = path + '/' + self.index
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
            yield('doxygen', self.title)

    def get_search_results(self, req, keywords, filters):
        if not 'doxygen' in filters:
            return

        # We have to search for the raw bytes...
        keywords = [k.encode(self.encoding) for k in keywords]

        for doc in os.listdir(self.base_path):
            # Search in documentation directories
            path = os.path.join(self.base_path, doc)
            if os.path.isdir(path):
                index = os.path.join(path, 'search.idx')
                if os.path.exists(index):
                    creation = os.path.getctime(index)
                    for result in  self._search_in_documentation(doc, keywords):
                        result['url'] =  req.href.doxygen(doc) + '/' \
                          + result['url']
                        yield result['url'], result['name'], creation, \
                          'doxygen', None

            # Search in common documentation directory
            index = os.path.join(self.base_path, 'search.idx')
            if os.path.exists(index):
                creation = os.path.getctime(index)
                for result in self._search_in_documentation('', keywords):
                    result['url'] =  req.href.doxygen() + '/' + \
                      result['url']
                    yield result['url'], result['name'], creation, 'doxygen', \
                      None

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('doxygen', self._doxygen_link)

    def get_wiki_syntax(self):
        return []

    # internal methods
    def _search_in_documentation(self, doc, keywords):
        # Open index file for documentation
        index = os.path.join(self.base_path, doc, 'search.idx')
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
                        matches.append({'word': word, 'match': w,
                         'index': statIdx, 'full': len(low) == len(w)})
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
                        results.append({'idx': idx, 'freq': freq >> 1,
                          'hi': freq & 1, 'multi': multiplier})
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
                        results[i]['rank'] = float(freq*multi + totalFreqLo) \
                          / float(totalFreq)
                    else:
                        results[i]['rank'] = float(freq*multi) \
                          / float(totalFreq)

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
            return html.a(label, href = formatter.href.doxygen(params),
              title = params)
        else:
            return html.a(label, href = formatter.href.doxygen(),
              title = params, class_ = 'missing')
