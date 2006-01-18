# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
#

from __future__ import generators

import os
import time
import posixpath
import re

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.Search import ISearchSource
from trac.util import Markup

def compare_rank(x, y):
    if x['rank'] == y['rank']:
        return 0
    elif x['rank'] > y['rank']:
        return -1
    
    return 1

class DoxygenPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, ISearchSource)

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'doxygen'
    def get_navigation_items(self, req):
        yield ('mainnav', 'doxygen', Markup('<a href="%s">Doxygen</a>', self.env.href.doxygen()))

    # IRequestHandler methods

    def match_request(self, req):
        if req.path_info == '/doxygen':
            req.args['path'] = ''.join([self.config.get('doxygen', 'path'), '/main.html'])
            return True
        elif re.match(r'''^/.*[.]html$''', req.path_info):
            self.log.debug("path = %s" % (req.path_info))
            path = ''.join([self.config.get('doxygen', 'path'), req.path_info])
            req.args['path'] = path
            return os.path.exists(path)
        
        return False

    def process_request(self, req):
        req.hdf['doxygen.path'] = req.args['path']
        return 'doxygen.cs', 'text/html'

    # ITemplateProvider methods

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # ISearchProvider methods
    
    def get_search_filters(self, req):
        yield('doxygen', 'Doxygen')

    def get_search_results(self, req, query, filters):
        if not 'doxygen' in filters:
            return
        if query[0] == query[-1] == "'" or query[0] == query[-1] == '"':
            keywords = [query[1:-1]]
        else:
            keywords = query.split(' ')
  
        path = self.config.get('doxygen', 'path')
        path = ''.join([path, '/search.idx'])

        if os.path.exists(path): 
            fd = open(path)
            
            results = []
            for keyword in keywords:
                results += self._search(fd, keyword)
            
            results.sort(compare_rank)            
            
            # use the creation time for the search.idx file for all results      
            creation = os.path.getctime(path)

            for result in results:
                yield result['url'], result['name'], creation, 'doxygen', None
    
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
            return ""
        result = byte
        while byte != '\0':
            byte = fd.read(1)
            result = ''.join([result, byte])
    
        return result

