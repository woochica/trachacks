from trac.web.api import ITemplateStreamFilter
from trac.core import *

from genshi.filters.transform import Transformer, INSIDE
from genshi.core import *

import os

class ReportFilter(Component):
    implements(ITemplateStreamFilter)

    def match_stream(self, req, method, filename, stream, data):
        return filename == 'report_view.html'

    @staticmethod
    def _filter(marked_stream, prefix_len):
        """A filter for marked streams containing xhtml table rows.
        """
        projectname = None
        foundproject = False
        
        for mark,(kind,data,pos) in marked_stream:
            if mark is INSIDE:
                if kind == 'START':
                    name,attrs = data

                    if name.localname == u'td' and attrs.get('class') == 'project':
                        foundproject = True

                    elif name.localname == 'a' and projectname:
                        url = attrs.get('href')
                        if url and url.startswith('/'):
                            components = url.split('/')
                            components = components[:prefix_len] \
                                         + ['projects',projectname] \
                                         + components[prefix_len:]

                            attrs = attrs - ('href', url) \
                                    | [(QName('href'), '/'.join(components)),]
                            data = name,attrs

                elif kind == 'TEXT' and foundproject:
                    projectname = data.strip()
                    foundproject = False

            yield mark,(kind,data,pos)
            
    def filter_stream(self, req, method, filename, stream, data):
        prefix_len = req.abs_href().rstrip('/').count('/') - 1
        return stream | Transformer(
            '//table[@class="listing tickets"]/tbody/tr'
            ).apply(lambda s: self._filter(s,prefix_len))
            
