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
            # Get config variables
            title = self.env.config.get('doxygen', 'title', 'Doxygen')

            # Return mainnav buttons
            yield 'mainnav', 'doxygen', Markup('<a href="%s">%s</a>' % \
              (self.env.href.doxygen() + '/', title))

    # IRequestHandler methods

    def match_request(self, req):
        # Get config variables
        base_path = self.config.get('doxygen', 'path', '/var/lib/trac/doxygen')
        ext = self.config.get('doxygen', 'ext', 'htm html png')
        ext = '|'.join(ext.split(' '))

        # Match index
        if re.match('^/doxygen/$', req.path_info):
            req.args['path'] = base_path
            req.args['type'] = 'index'
            return True

        # Match searching request
        if re.match('^/doxygen/search.php$', req.path_info):
            return True

        # Match request if requested file exists
        elif re.match(r'''^/doxygen/.*[.](%s)$''' % (ext), req.path_info):
            file = re.sub('^/doxygen', '', req.path_info)
            path = base_path + file
            req.args['path'] = path
            req.args['type'] = mimetypes.guess_type(path)[0]
            return os.path.exists(path)
        else:
            return False

    def process_request(self, req):
        # Get request arguments
        path = req.args.get('path')
        type = req.args.get('type')

        # Get config variables
        index =  self.config.get('doxygen', 'index', 'main.html')
        wiki_index = self.config.get('doxygen', 'wiki_index', None)

        # Retrun apropriate content to type or search request
        if req.args.has_key('query'):
            req.redirect('%s?q=%s&doxygen=on' % (self.env.href.search(),
              req.args.get('query')))
            return None, None
        elif type == 'index':
            if wiki_index:
                # Get access to database
                db = self.env.get_db_cnx()
                cursor = db.cursor()

                # Get wiki index
                sql = "SELECT text FROM wiki WHERE name = %s"
                cursor.execute(sql, (wiki_index,))
                text = Markup(system_message('Error', 'Wiki page %s does not exists' % (wiki_index)))
                for row in cursor:
                    text = wiki_to_html(row[0], self.env, req)

                # Display wiki index page
                req.hdf['doxygen.text'] = text
                return 'doxygen.cs', 'text/html'
            else:
                add_stylesheet(req, 'doxygen/css/doxygen.css')
                req.hdf['doxygen.path'] = path + '/' + index
                return 'doxygen.cs', 'text/html'
        elif type == 'text/html':
            add_stylesheet(req, 'doxygen/css/doxygen.css')
            req.hdf['doxygen.path'] = path
            return 'doxygen.cs', type
        else:
            req.send_file(path, type)
            return None, None

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

        path = self.config.get('doxygen', 'path')
        path = os.path.join(path, 'search.idx')

        if os.path.exists(path):
            fd = open(path)

            results = []
            for keyword in keywords:
                results += self._search(fd, keyword)

            results.sort(compare_rank)

            # use the creation time for the search.idx file for all results
            creation = os.path.getctime(path)

            for result in results:
                yield 'doxygen/' + result['url'], result['name'], creation, 'doxygen', None

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('doxygen', self._doxygen_link)

    def get_wiki_syntax(self):
        return []


    # internal methods

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
        byte = fd.read(1)
        if byte == '\0':
            return ''
        result = byte
        while byte != '\0':
            byte = fd.read(1)
            result = ''.join([result, byte])

        return result

    def _doxygen_link(self, formatter, ns, params, label):
        if ns == 'doxygen':
            return '<a href="%s" title="%s">%s</a>' % \
              (self.env.href.doxygen(params), params, label)
        else:
            return '<a href="%s" class="missing">%s?</a>' % \
              (self.env.href.doxygen(), label)
