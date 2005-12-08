"""
$Id$
$HeadURL$

Copyright (c) 2005 Peter Kropf. All rights reserved.

Module documentation goes here.
"""



__version__   = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import sha
import os
import sys

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util import escape



class GraphvizMacro(Component):
    """
    Blah, blah, blah.
    """
    implements(IWikiMacroProvider)

    # Available formats and processors, default first (dot/png)
    processors = ['dot', 'neato', 'twopi', 'circo', 'fdp']
    formats    = ['png', 'gif', 'jpg', 'svg', 'svgz']


    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        for p in ['.' + p for p in GraphvizMacro.processors] + ['']: 
            for f in ['/' + f for f in GraphvizMacro.formats] + ['']:
                yield 'graphviz' + p + f


    def get_macro_description(self, name):
        """Return a plain text description of the macro with the specified name."""
        return inspect.getdoc(GraphvizMacro)


    def render_macro(self, req, name, content):
        """Return the HTML output of the macro.

        req - ?
        
        name - Wiki macro command that resulted in this method being
               called. In this case, it should be 'graphviz', followed
               (or not) by the processor name, then by an output
               format, as following: graphviz.<processor>/<format>

               Valid processor names are: dot, neato, twopi, circo,
               and fdp.  The default is dot.

               Valid output formats are: jpg, png, gif, svg and svgz.
               The default is the value specified in the out_format
               configuration parameter. If out_format is not specified
               in the configuration, then the default is png.

               examples: graphviz.dot/png   -> dot    png
                         graphviz.neato/jpg -> neato  jpg
                         graphviz.circo     -> circo  png
                         graphviz/svg       -> dot    svg

        content - The text the user entered for the macro to process.

        todo: allow the admin to configure cache size or count limits.

        todo: allow the user to set the default graph, node and edge attributes.

        todo: show the user any errors that graphviz may produce.
        """

        trouble, msg = self.check_config()
        if trouble:
            return msg.getvalue()

        cache_dir  = self.config.get('graphviz', 'cache_dir')
        prefix_url = self.config.get('graphviz', 'prefix_url')
        tmp_dir    = self.config.get('graphviz', 'tmp_dir')
        cmd_path   = self.config.get('graphviz', 'cmd_path')
        out_format = self.config.get('graphviz', 'out_format')

        buf = StringIO()

        # Extract processor and format from name
        d_sp = name.split('.')
        s_sp = name.split('/')
        if len(d_sp) > 1:
            s_sp = d_sp[1].split('/')
            if len(s_sp) > 1:
                out_format = s_sp[1]
            else:
                out_format = GraphvizMacro.formats[0]
            proc = s_sp[0]
        elif len(s_sp) > 1:
            proc   = GraphvizMacro.processors[0]
            out_format = s_sp[1]
        else:
            proc   = GraphvizMacro.processors[0]
            out_format = GraphvizMacro.formats[0]
	
        if proc in GraphvizMacro.processors:
            cmd = os.path.join(cmd_path, proc)
        else:
            buf.write('<p>Graphviz macro processor error: requested processor <b>(%s)</b> not found.</p>' % proc)
            return buf.getvalue()
           
        if out_format not in GraphvizMacro.formats:
            buf.write('<p>Graphviz macro processor error: requested format <b>(%s)</b> not valid.</p>' % out_format)
            return buf.getvalue()

        sha_key    = sha.new(content).hexdigest()
        tmp_name   = os.path.join(tmp_dir, sha_key + '_' + out_format + '.' + proc)
        cache_name = os.path.join(cache_dir, sha_key + '.' + out_format)

        if not os.path.exists(cache_name):
            f = open(tmp_name, 'w')
            f.writelines(content)
            f.close()

            os.system(cmd + ' -T' + out_format + ' -o' + cache_name + ' ' + tmp_name)

        if out_format in ('svg', 'svgz'):
            buf.write('<object data="%s/%s" type"image/svg+xml" width="100%%" height="100%%"/>' % (prefix_url, sha_key + '.' + out_format))
        else:
            buf.write('<img src="%s/%s"/>' % (prefix_url, sha_key + '.' + out_format))

        return buf.getvalue()


    def check_config(self):
        buf = StringIO()
        trouble = False
        if sys.platform == 'win32':
            exe_suffix = '.exe'
        else:
            exe_suffix = ''

        buf.write('<p>Graphviz macro processor not configured correctly. Please fix the configuration before continuing.</p>')
        if 'graphviz' not in self.config.sections():
            buf.write('<p>The <b>graphviz</b> section was not found.</p>')
            trouble = True
        else:
            for field in ['cache_dir', 'cmd_path', 'prefix_url', 'tmp_dir']:
                if not self.config.parser.has_option('graphviz', field):
                    buf.write('<p>The <b>graphviz</b> section is missing the <b>%s</b> field.</p>' % field)
                    trouble = True

            for name in ['cache_dir', 'tmp_dir']:
                path = self.config.get('graphviz', name)
                if not os.path.exists(path):
                    buf.write('<p>The <b>%s</b> is set to <b>%s</b> but that path does not exist.' % (name, path))
                    trouble = True


            if self.config.parser.has_option('graphviz', 'cmd_path'):
                cmd_path = self.config.get('graphviz', 'cmd_path')
                for name in GraphvizMacro.processors:
                    exe_path = os.path.join(cmd_path, name) + exe_suffix
                    if not os.path.exists(exe_path):
                        buf.write('<p>The <b>%s</b> program was not found in the <b>%s</b> directory.</p>' % (name, cmd_path))
                        trouble = True
        
            if self.config.parser.has_option('graphviz', 'out_format'):
                out_format = self.config.get('graphviz', 'out_format')
                if out_format not in ('svg', 'svgz', 'jpg', 'png', 'gif'):
                    buf.write('<p>The specified formt (<b>%s</b>) is not recognized as a valid graphviz output format.</p>' % output_format)
                    trouble = True
            else:
                out_format = 'png'

        return trouble, buf
