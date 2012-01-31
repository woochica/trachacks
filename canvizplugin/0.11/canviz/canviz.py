# -*- coding: utf-8 -*-
#
# Released under BSD license
#
# Copyright (C) 2008,2009 ActiveState
# All rights reserved.
#
# Author: Shane Caraveo <shanec@activestate.com>
#
# Most probably you will want to add following lines to your configuration file:
#
#   [components]
#   canviz.* = enabled


import inspect
import locale
import os
import re
import sha
import subprocess
import sys
import simplejson

from genshi.builder import Element, tag
from genshi.core import Markup

from trac.config import BoolOption, IntOption, Option
from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
        add_stylesheet, add_script, add_ctxtnav
from trac.util import escape
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import extract_link


class Canviz(Component):
    """
    Canviz provides a JavaScript canvas based renderer for graphviz files
    """
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, ITemplateProvider, IRequestHandler)
    jquery_noconflict = True
    # Available formats and processors, default first (dot/png)
    Processors = ['dot', 'neato', 'twopi', 'circo', 'fdp']

    # IRequestHandler methods
    def match_request(self, req):
        add_script(req, 'common/js/noconflict.js')
        return False

    def process_request(self, req):
        return None, {}, None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return a list of directories containing the provided ClearSilver
        templates.
        """
        #from pkg_resources import resource_filename
        #return [resource_filename(__name__, 'templates')]
        return []

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('canviz', resource_filename(__name__, 'htdocs'))]

    # IHTMLPreviewRenderer methods

    def get_quality_ratio(self, mimetype):
        self.log.error(mimetype)
        if mimetype in self.MIME_TYPES:
            return 2
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        ext = filename.split('.')[1]
        name = ext == 'canviz' and 'canviz' or 'canviz.%s' % ext
        text = hasattr(content, 'read') and content.read() or content
        return self.render_macro(context, name, text)

    # IWikiMacroProvider methods

    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        for p in ['.' + p for p in Canviz.Processors] + ['']: 
            yield 'canviz%s' % (p)


    def get_macro_description(self, name):
        """
        Return a plain text description of the macro with the
        specified name. Only return a description for the base
        canviz macro. 
        """
        if name == 'canviz':
            return inspect.getdoc(Canviz)
        else:
            return None


    def expand_macro(self, formatter, name, content):
        """Return the HTML output of the macro.

        formatter - ?

        name - Wiki macro command that resulted in this method being
               called. In this case, it should be 'canviz', followed
               (or not) by the processor name as following: canviz.<processor>

               Valid processor names are: dot, neato, twopi, circo,
               and fdp.  The default is dot.

               examples: canviz.dot   -> dot    
                         canviz.neato -> neato  
                         canviz.circo -> circo  
                         canviz       -> dot    

        canviz uses the XDOT format.  To convert from DOT to XDOT you can
        use the dot command:
        
                echo "digraph G {Hello->World}" | dot -Txdot -otemp.xdot
        
        content - The text the user entered for the macro to process.
        """
        req = formatter.req

        ## Extract processor and format from name
        d_sp = name.split('.')
        processor = 'dot'
        if len(d_sp) > 1:
            processor = d_sp[1]

        if processor not in Canviz.Processors:
            self.log.error('render_macro: requested processor (%s) not found.' %
                           processor)
            return self._error_div('requested processor (%s) not found.' % 
                                  processor)

        # add the canviz js library
        add_stylesheet(req, 'canviz/canviz.css')
        add_script(req, 'canviz/prototype.js')
        add_script(req, 'canviz/path.js')
        add_script(req, 'canviz/canviz.js')
        add_script(req, 'canviz/x11colors.js')
        
        div = tag.div(id="canviz_container")
        div(tag.div(id="graph_container"))
        js = tag.script(type="text/javascript")
        the_data = simplejson.dumps(content)
        js_content = """
        function html_entity_decode(str)
        {
            try
                {
                        var  tarea=document.createElement('textarea');
                        tarea.innerHTML = str; return tarea.value;
                        tarea.parentNode.removeChild(tarea);
                }
                catch(e)
                {
                        //for IE add <div id="htmlconverter" style="display:none;"></div> to the page
                        document.getElementById("htmlconverter").innerHTML = '<textarea id="innerConverter">' + str + '</textarea>';
                        var content = document.getElementById("innerConverter").value;
                        document.getElementById("htmlconverter").innerHTML = "";
                        return content;
                }
        }
        jQuery(document).ready(function() {
            var content = %s;
            var canviz = new Canviz('graph_container');
            canviz.parse(html_entity_decode(content));
        });
        """ % (the_data,)
        js(js_content)
        div(js)
        div(tag.div(id="debug_output"))
        return div

    # Private methods
    def _error_div(self, msg):
        """Display msg in an error box, using Trac style."""
        if isinstance(msg, str):
            msg = to_unicode(msg)
        self.log.error(msg)
        if isinstance(msg, unicode):
            msg = tag.pre(escape(msg))
        return tag.div(
                tag.strong(_("Canviz macro processor has detected an error. "
                             "Please fix the problem before continuing.")),
                msg, class_="system-message")
