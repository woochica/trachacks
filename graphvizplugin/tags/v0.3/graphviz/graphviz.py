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

    def __init__(self):
        self.log.debug('id: %s' % str(__id__))
        self.log.debug('processors: %s' % str(GraphvizMacro.processors))
        self.log.debug('formats: %s' % str(GraphvizMacro.formats))


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

        self.log.debug('render_macro.cache_dir: %s' % cache_dir)
        self.log.debug('render_macro.prefix_url: %s' % prefix_url)
        self.log.debug('render_macro.tmp_dir: %s' % tmp_dir)
        self.log.debug('render_macro.cmd_path: %s' % cmd_path)
        self.log.debug('render_macro.out_format: %s' % out_format)

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
            self.log.debug('render_macro: requested processor (%s) not found.' % proc)
            buf.write('<p>Graphviz macro processor error: requested processor <b>(%s)</b> not found.</p>' % proc)
            return buf.getvalue()
           
        if out_format not in GraphvizMacro.formats:
            self.log.debug('render_macro: requested format (%s) not found.' % out_format)
            buf.write('<p>Graphviz macro processor error: requested format <b>(%s)</b> not valid.</p>' % out_format)
            return buf.getvalue()

        sha_key    = sha.new(content).hexdigest()
        tmp_name   = os.path.join(tmp_dir, sha_key + '_' + out_format + '.' + proc)
        cache_name = os.path.join(cache_dir, sha_key + '.' + out_format)

        if not os.path.exists(cache_name):
            self.clean_cache()
            self.log.debug('render_macro: creating tmp file: %s' % tmp_name)
            f = open(tmp_name, 'w')
            f.writelines(content)
            f.close()

            full_cmd = cmd + ' -T' + out_format + ' -o' + cache_name + ' ' + tmp_name
            self.log.debug('render_macro: running command %s' % full_cmd)
            os.system(full_cmd)

            os.unlink(tmp_name)

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


    def clean_cache(self):
        """
        The cache manager (clean_cache) is an attempt at keeping the
        cache directory under control. When the cache manager
        determines that it should clean up the cache, it will delete
        files based on the file access time. The files that were least
        accessed will be deleted first.

        The graphviz section of the trac configuration file should
        have an entry called cache_manager to enable the cache
        cleaning code. If it does, then the cache_max_size,
        cache_min_size, cache_max_count and cache_min_count entries
        must also be there.
        """

        if self.config.parser.has_option('graphviz', 'cache_manager'):
            max_size  = int(self.config.get('graphviz', 'cache_max_size'))
            min_size  = int(self.config.get('graphviz', 'cache_min_size'))
            max_count = int(self.config.get('graphviz', 'cache_max_count'))
            min_count = int(self.config.get('graphviz', 'cache_min_count'))
            cache_dir = self.config.get('graphviz', 'cache_dir')

            self.log.debug('clean_cache.cache_dir: %s' % cache_dir)
            self.log.debug('clean_cache.max_count: %d' % max_count)
            self.log.debug('clean_cache.min_count: %d' % min_count)
            self.log.debug('clean_cache.max_size: %d' % max_size)
            self.log.debug('clean_cache.min_size: %d' % min_size)

            # os.stat gives back a tuple with: st_mode(0), st_ino(1),
            # st_dev(2), st_nlink(3), st_uid(4), st_gid(5),
            # st_size(6), st_atime(7), st_mtime(8), st_ctime(9)

            entry_list = {}
            atime_list = {}
            size_list = {}
            count = 0
            size = 0

            for name in os.listdir(cache_dir):
                self.log.debug('clean_cache.entry: %s' % name)
                entry_list[name] = os.stat(os.path.join(cache_dir, name))

                atime_list.setdefault(entry_list[name][7], []).append(name)
                count = count + 1

                size_list.setdefault(entry_list[name][6], []).append(name)
                size = size + entry_list[name][6]

            atime_keys = atime_list.keys()
            atime_keys.sort()

            self.log.debug('clean_cache.atime_keys: %s' % atime_keys)
            self.log.debug('clean_cache.count: %d' % count)
            self.log.debug('clean_cache.size: %d' % size)
        
            # In the spirit of keeping the code fairly simple, the
            # clearing out of files from the cache directory may
            # result in the count dropping below cache_min_count if
            # multiple entries are have the same last access
            # time. Same for cache_min_size.
            if count > max_count or size > max_size:
                while len(atime_keys) and (min_count < count or min_size < size):
                    key = atime_keys.pop(0)
                    for file in atime_list[key]:
                        self.log.debug('clean_cache.unlink: %s' % file)
                        os.unlink(os.path.join(cache_dir, file))
                        count = count - 1
                        size = size - entry_list[file][6]
        else:
            self.log.debug('clean_cache: cache_manager not set')
