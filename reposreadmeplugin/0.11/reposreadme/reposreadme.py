# -*- coding: utf-8 -*-
"""
Trac plugin that renders any 'README(.*)' files when browsing
directories in repository.

License: BSD
(c) 2009 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.mimeview.api import Mimeview
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet
from trac.util.text import to_unicode

__all__ = ['ReposReadMePlugin']

class ReposReadMePlugin(Component):
    
    implements(ITemplateStreamFilter)

    # ITemplateStreamFilter method

    def filter_stream(self, req, method, template, stream, data):
        if not (template == 'browser.html' and data.get('dir')):
            # Only interested if browsing directories
            return stream
        repos = self.env.get_repository()
        rev = req.args.get('rev', None)
        initial_space = False
        for entry in data['dir']['entries']:
            try:
                if not entry.isdir and entry.name.lower().startswith('readme'):
                    # Render any file starting with 'readme'
                    node = repos.get_node(entry.path, rev)
                    output = self._render_file(req, data['context'], repos,
                                                node, rev=rev)
                    if output:
                        insert_where = Transformer(
                                    "//div[@id='content']/div[@id='help']")
                        insert_what = tag.div(
                                        not initial_space and tag.br() or None,
                                        output['rendered'],
                                        id="readme", class_="searchable",
                                        title=entry.name)
                        stream = stream | insert_where.before(insert_what)
                        initial_space = True
            except Exception, e:
                # Just log and ignore any kind of error (permissions and more)
                self.log.debug(to_unicode(e))
        return stream

    # Internal

    def _render_file(self, req, context, repos, node, rev=None):
        """ trac.versioncontrol.web_ui.browser.BrowserModule._render_file()
        copy with just the essentials needed for our purpose. """

        req.perm(context.resource).require('FILE_VIEW')

        mimeview = Mimeview(self.env)
        # MIME type detection
        CHUNK_SIZE = 4096
        content = node.get_content()
        chunk = content.read(CHUNK_SIZE)
        mime_type = node.content_type
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = mimeview.get_mimetype(node.name, chunk) or \
                        mime_type or 'text/plain'

        self.log.debug("Rendering ReposReadMe of node %s@%s with mime-type %s"
                       % (node.name, str(rev), mime_type))
        del content # the remainder of that content is not needed
        add_stylesheet(req, 'common/css/code.css')

        annotations = []
        force_source = False
        raw_href = ''
        return mimeview.preview_data(context, node.get_content(),
                                             node.get_content_length(),
                                             mime_type, node.created_path,
                                             raw_href,
                                             annotations=annotations,
                                             force_source=force_source)
