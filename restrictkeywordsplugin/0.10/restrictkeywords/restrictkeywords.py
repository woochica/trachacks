#
# Copyright (C) 2008 Thomas Tressieres <thomas.tressieres@free.fr>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Tressieres Thomas <thomas.tressieres@free.fr>


from trac import util
from trac.core import *
from trac.config import Option, BoolOption
from trac.web.chrome import ITemplateProvider, INavigationContributor, \
                            add_stylesheet, add_link, add_script
from trac.ticket import ITicketManipulator
from trac.web.main import IRequestHandler
from trac.util import Markup
import os, time, fnmatch, re, urllib, string



header_html = """
    <center>
	<a href="#" onclick="expandAll('idTree');return false">Expand all</a>
	<a href="#" onclick="collapseAll('idTree');return false">Collapse all</a>
	</center>
    <br><br>
"""

footer_html = """
    <br>
    <center>
	<input type="button" value="Submit" onclick="parent.document.getElementById('keywords').value = toKeywordsString('idTree');var div = parent.document.getElementById('keyword_tree_div');div.style.display = 'none';return false" />
	<input type="button" value="Cancel" onclick="var div = parent.document.getElementById('keyword_tree_div');div.style.display = 'none';return false" />
	</center>
	<script type="text/javascript">
	initTree('idTree');
	</script>
"""


class RestrictedKeywordsPlugin(Component):
    """A plugin to integrate Restricted Keywords into Trac"""
    implements(ITicketManipulator,
               INavigationContributor,
               IRequestHandler,
               ITemplateProvider)

    html_file = Option('restrictkeywords', 'filename', '',
                       """HTML file name containing tree's representation of available keywords.""")
    keywords_mandatory = BoolOption('restrictkeywords', 'mandatory', 'true',
                                    """Boolean to specify if the ticket(s field can be empty.""")

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return '' # This is never called

    def get_navigation_items(self, req):
        self.log.debug("RestrictedKeywordsPlugin::get_navigation_items")
        if req.path_info.startswith('/newticket'):
            self._open_html_file('')
            evil_js = '/'.join(['rk_htdoc','js','restrict-keyword.js'])
            add_stylesheet(req, 'rk_htdoc/css/keyword-restrict-tree.css')
            add_script(req, evil_js)
            self._add_js(req, self._make_js(req))
        return [] # This returns no buttons


    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('rk_htdoc', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # IRequestHandler methods
    def match_request(self, req):
        import re
        found = re.match(r'/restrictkeywords(?:/?\?log=|/?)(.*)$', req.path_info)
        if found:
            self.log.debug("* match_request  %s ", (req.path_info))
            return 1

    def process_request(self, req):
        req.perm.assert_permission('CHANGESET_VIEW')
        #self.log.debug("* process_request  %s ", (self.line))
        req.send_response(200)
        req.send_header('Content-Type', 'text/plain')
        req.end_headers()
        req.write(self.line)
        return


    # ITicketManipulator methods
    def prepare_ticket(req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.

        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""

        if self.keywords_mandatory:
            self.log.debug('fields values: "%s" ', (ticket.values))
            f = ticket.values['keywords']
            if f == '':
                return [("keywords", "you have to enter some keywords")]
        return []


    # Internal methods
    def _add_js(self, req, data):
        """Add javascript to a page via hdf['project.footer']"""
        footer = req.hdf['project.footer']
        footer += data
        req.hdf['project.footer'] = Markup(footer)

    def _make_js(self, req):
        """Generate the needed Javascript."""
        js = "add_restrictkeywords_button('%s/%s');\n" % (req.base_url, 'restrictkeywords')
        return """<script type="text/javascript">%s</script>"""%js

    def _open_html_file(self, filename):
        f = open(self.html_file)
        self.lines = f.readlines()
        self.line = ''.join(x for x in self.lines)
        self.line = header_html + self.line;
        self.line += footer_html;
