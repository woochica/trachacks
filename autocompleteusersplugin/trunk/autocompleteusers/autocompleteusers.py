# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Jeff Hammel
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
import fnmatch

from pkg_resources import resource_filename

from trac.core import *

from trac.config import ListOption
from trac.web.api import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web.chrome import add_script
from trac.web.chrome import add_stylesheet
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider 
from trac.web.chrome import ITemplateStreamFilter

class AutocompleteUsers(Component):

    implements(IRequestHandler, IRequestFilter, ITemplateProvider, ITemplateStreamFilter)
    selectfields = ListOption('autocomplete', 'fields', default='',
                              doc='select fields to transform to autocomplete text boxes')
    prefix = "autocompleteusers" # prefix for htdocs -- /chrome/prefix/...    

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return req.path_info.rstrip('/') == '/users'

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

        query = req.args.get('q', '').lower()
        chrome = Chrome(self.env)

        ### user names, email addressess, full names
        users = []
        USER=0; NAME=1; EMAIL=2 # indices 

        # instead of known_users, could be
        # perm = PermissionSystem(self.env)
        # owners = perm.get_users_with_permission('TICKET_MODIFY')
        # owners.sort()
        # see: http://trac.edgewall.org/browser/trunk/trac/ticket/default_workflow.py#L232

        for user_data in self.env.get_known_users(): 
            user_data = [ i is not None and chrome.format_author(req, i) or ''
                          for i in user_data ]
            for index, field in enumerate((USER, EMAIL, NAME)): # ordered by how they appear
                value = user_data[field].lower()

                if value.startswith(query):
                    users.append((2-index, user_data)) # 2-index is the sort key
                    break
                if field == NAME:
                    lastnames = value.split()[1:]
                    if sum(name.startswith(query) for name in lastnames):
                        users.append((2-index, user_data)) # 2-index is the sort key
                        break

            
        users = [ '%s|%s|%s' % (user[USER], 
                                 user[EMAIL] and '&lt;%s&gt; ' % user[EMAIL] or '',
                                 user[NAME])
                  for value, user in sorted(users) ] # value unused (placeholder need for sorting)

        req.send('\n'.join(users).encode('utf-8'), 'text/plain')


    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """

        return [(self.prefix, resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return []

    ### methods for IRequestFilter

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
        if template == 'ticket.html':
            add_stylesheet(req, '%s/css/autocomplete.css' % self.prefix)
            add_script(req, '%s/js/autocomplete.js' % self.prefix)
            restrict_owner = self.env.config.getbool('ticket', 'restrict_owner')
            add_script(req, '%s/js/format_item.js' % self.prefix)
            if req.path_info.rstrip() == '/newticket':
                add_script(req, '%s/js/autocomplete_newticket_cc.js' % self.prefix)
                if not restrict_owner:
                    add_script(req, '%s/js/autocomplete_newticket.js' % self.prefix)
            else:
                add_script(req, '%s/js/autocomplete_ticket_cc.js' % self.prefix)
                if not restrict_owner:
                    add_script(req, '%s/js/autocomplete_ticket.js' % self.prefix)
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

    ### methods for ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """
        if filename == 'ticket.html':
            fields = [ field['name'] for field in data['ticket'].fields 
                       if field['type'] == 'select' ]
            fields = set(sum([ fnmatch.filter(fields, pattern)
                               for pattern in self.selectfields ], []))
            
        return stream
