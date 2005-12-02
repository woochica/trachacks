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

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util import escape


class GraphvizMacro(Component):
    """
    Blah, blah, blah.
    """
    implements(IWikiMacroProvider)


    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        yield 'graphviz'
        yield 'graphviz.dot'
        yield 'graphviz.neato'
        yield 'graphviz.twopi'
        yield 'graphviz.circo'
        yield 'graphviz.fdp'


    def get_macro_description(self, name):
        """Return a plain text description of the macro with the specified name."""
        return inspect.getdoc(GraphvizMacro)


    def render_macro(self, req, name, content):
        """Return the HTML output of the macro.

        req - ?
        
        name - Wiki macro command that resulted in this method being
        called. In this case, it should be one of graphviz,
        graphviz.dot, graphviz.neato, graphviz.twopi, graphviz.circo
        or graphviz.fdp.

        content - The text the user entered for the macro to process.

        todo: allow the admin to configure cache size or count limits.

        todo: allow the user to specify the image type.

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

        cmd = {'graphviz':       os.path.join(cmd_path, 'dot'),
               'graphviz.dot':   os.path.join(cmd_path, 'dot'),
               'graphviz.neato': os.path.join(cmd_path, 'neato'),
               'graphviz.twopi': os.path.join(cmd_path, 'twopi'),
               'graphviz.circo': os.path.join(cmd_path, 'circo'),
               'graphviz.fdp':   os.path.join(cmd_path, 'fdp'),
               }[name]

        sha_key    = sha.new(content).hexdigest()
        tmp_name   = os.path.join(tmp_dir, sha_key + '.' + name)
        cache_name = os.path.join(cache_dir, sha_key + '.png')

        if not os.path.exists(cache_name):
            f = open(tmp_name, 'w')
            f.writelines(content)
            f.close()

            os.system(cmd + ' -Tpng -o' + cache_name + ' ' + tmp_name)

        buf = StringIO()
        buf.write('<img src="%s/%s"/>' % (prefix_url, sha_key + '.png'))

        return buf.getvalue()


    def check_config(self):
        buf = StringIO()
        trouble = False
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
                for name in ['dot', 'neato', 'twopi', 'circo', 'fdp']:
                    if not os.path.exists(os.path.join(cmd_path, name)):
                        buf.write('<p>The <b>%s</b> program was not found in the <b>%s</b> directory.</p>' % (name, cmd_path))
                        trouble = True
        return trouble, buf
