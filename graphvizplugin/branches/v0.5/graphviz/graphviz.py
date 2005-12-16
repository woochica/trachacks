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
import re

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util import escape
from trac.wiki.formatter import wiki_to_oneliner



class GraphvizMacro(Component):
    """
    Blah, blah, blah.
    """
    implements(IWikiMacroProvider)

    # Available formats and processors, default first (dot/png)
    processors = ['dot', 'neato', 'twopi', 'circo', 'fdp']
    bitmap_formats = ['png', 'jpg', 'gif']
    vector_formats = ['svg', 'svgz']
    formats = bitmap_formats + vector_formats 

    def __init__(self):
        self.log.info('id: %s' % str(__id__))
        self.log.info('processors: %s' % str(GraphvizMacro.processors))
        self.log.info('formats: %s' % str(GraphvizMacro.formats))


    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        for p in ['.' + p for p in GraphvizMacro.processors] + ['']: 
            for f in ['/' + f for f in GraphvizMacro.formats] + ['']:
                yield 'graphviz%s%s' % (p, f)


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
        """

        self.log.debug('dir(req): %s' % str(dir(req)))
        self.log.debug('req.args: %s' % str(req.args))
        self.log.debug('req.base_url: %s' % str(req.base_url))

        self.base_url = req.base_url
        # check and load the configuration
        trouble, msg = self.load_config()
        if trouble:
            return msg.getvalue()

        buf = StringIO()


        ## Extract processor and format from name
        l_proc = l_out_format = ''

        # first try with the RegExp engine
        try: 
            m = re.match('graphviz\.?([a-z]*)\/?([a-z]*)', name)
            (l_proc, l_out_format) = m.group(1, 2)

        # or use the string.split method
        except:
            (d_sp, s_sp) = (name.split('.'), name.split('/'))
            if len(d_sp) > 1:
                s_sp = d_sp[1].split('/')
                if len(s_sp) > 1:
                    l_out_format = s_sp[1]
                l_proc = s_sp[0]
            elif len(s_sp) > 1:
                l_out_format = s_sp[1]
            
        # assign default values, if instance ones are empty
        self.out_format = (self.out_format, l_out_format)[bool(len(l_out_format))]
        self.processor  = (self.processor,  l_proc)      [bool(len(l_proc))]


        if self.processor in GraphvizMacro.processors:
            proc_cmd = os.path.join(self.cmd_path, self.processor)
        else:
            self.log.error('render_macro: requested processor (%s) not found.' % self.processor)
            buf.write('<p>Graphviz macro processor error: requested processor <b>(%s)</b> not found.</p>' % self.processor)
            return buf.getvalue()
           
        if self.out_format not in GraphvizMacro.formats:
            self.log.error('render_macro: requested format (%s) not found.' % self.out_format)
            buf.write('<p>Graphviz macro processor error: requested format <b>(%s)</b> not valid.</p>' % self.out_format)
            return buf.getvalue()

        sha_key  = sha.new(self.processor + content).hexdigest()
        img_name = '%s.%s.%s' % (sha_key, self.processor, self.out_format) # cache: hash.<dot>.<png>
        img_path = os.path.join(self.cache_dir, img_name)
        map_name = '%s.%s.map' % (sha_key, self.processor)       # cache: hash.<dot>.map
        map_path = os.path.join(self.cache_dir, map_name)

        # Check for URL="" presence in graph code
        URL_in_graph = 'URL=' in content

        # Create image if not in cache
        if not os.path.exists(img_path):
            self.clean_cache()

            self.log.debug('render_macro.URL_in_graph: %s' % str(URL_in_graph))
            if URL_in_graph: # translate wiki TracLinks in URL
                content = re.sub(r'URL="(.*)"', self.expand_wiki_links, content)

            # Antialias PNGs with rsvg, if requested
            if self.out_format == 'png' and self.png_anti_alias == True:
                # 1. SVG output
                cmd = '"%s" %s -Tsvg -o%s.svg' % (proc_cmd, self.processor_options, img_path)
                self.log.debug('render_macro: running command %s' % cmd)
                out, err = self.launch(cmd, content)
                if len(out) or len(err):
                    msg = 'The command\n   %s\nfailed with the the following output:\n%s\n%s' % (cmd, out, err)
                    return self.show_err(msg).getvalue()
                # 2. SVG to PNG rasterization
                cmd = '"%s" --dpi-x=%d --dpi-y=%d %s.svg %s' % (self.rsvg_path, self.dpi, self.dpi, img_path, img_path)
                self.log.debug('render_macro: running command %s' % cmd)
                out, err = self.launch(cmd, None)
                if len(out) or len(err):
                    msg = 'The command\n   %s\nfailed with the the following output:\n%s\n%s' % (cmd, out, err)
                    return self.show_err(msg).getvalue()
            
            else: # Render other image formats
                cmd = '"%s" %s -T%s -o%s' % (proc_cmd, self.processor_options, self.out_format, img_path)
                self.log.debug('render_macro: running command %s' % cmd)
                out, err = self.launch(cmd, content)
                if len(out) or len(err):
                    msg = 'The command\n   %s\nfailed with the the following output:\n%s\n%s' % (cmd, out, err)
                    return self.show_err(msg).getvalue()

            # Generate a map file for binary formats
            if URL_in_graph and self.out_format in GraphvizMacro.bitmap_formats:

                # Create the map if not in cache
                if not os.path.exists(map_path):
                    cmd = '"%s" %s -Tcmap -o%s' % (proc_cmd, self.processor_options, map_path)
                    self.log.debug('render_macro: running command %s' % cmd)
                    out, err = self.launch(cmd, content)
                    if len(out) or len(err):
                        msg = 'The command\n   %s\nfailed with the the following output:\n%s\n%s' % (cmd, out, err)
                        return self.show_err(msg).getvalue()


        # Generate HTML output
        # for SVG(z)
        if self.out_format in GraphvizMacro.vector_formats:
            try: # try to get SVG dimensions
                f = open(img_path, 'r')
                svg = f.readlines()
                f.close()
                svg = "".join(svg).replace('\n', '')
                w = re.search('width="([0-9]+)(.*?)" ', svg)
                h = re.search('height="([0-9]+)(.*?)"', svg)
                (w_val, w_unit) = w.group(1,2)
                (h_val, h_unit) = h.group(1,2)
                # Graphviz seems to underestimate height/width for SVG images,
                # so we have to adjust them. The correction factor seems to be constant.
                [w_val, h_val] = [ 1.35 * x for x in (int(w_val), int(h_val))]
                dimensions = 'width="%(w_val)s%(w_unit)s" height="%(h_val)s%(h_unit)s"' % locals()
            except:
                dimensions = 'width="100%" height="100%"'
            # insert SVG, IE compatibility
            buf.write('<!--[if IE]><embed src="%s/%s" type="image/svg+xml" %s></embed><![endif]--> ' % (self.prefix_url, img_name, dimensions))
            buf.write('<![if !IE]><object data="%s/%s" type="image/svg+xml" %s>SVG Object</object><![endif]>' % (self.prefix_url, img_name, dimensions))

        # for binary formats, add map
        elif URL_in_graph:
            f = open(map_path, 'r')
            map = f.readlines()
            f.close()
            map = "".join(map).replace('\n', '')
            buf.write('<map id="%s" name="%s">%s</map>' % (sha_key, sha_key, map))
            buf.write('<img id="%s" src="%s/%s" usemap="#%s" alt="GraphViz image"/>' % (sha_key, self.prefix_url, img_name, sha_key))

        else:
            buf.write('<img src="%s/%s"/>' % (self.prefix_url, img_name))

        return buf.getvalue()


    def expand_wiki_links(self, match):
        self.log.debug('expand_wiki_links.match.groups: %s' % str(match.groups()))
        
        wiki_url = match.groups()[0]                     # TracLink ([1], source:file/, ...)
        html_url = wiki_to_oneliner(wiki_url, self.env)  # <a href="http://someurl">...</a>
        href     = re.search('href="(.*?)"', html_url)   # http://someurl
        
        url      = 'URL="%s"' % href.groups()[0]
        self.log.debug('expand_wiki_links.url: %(url)s' % locals())

        return url


    def load_config(self):
        """Load the graphviz trac.ini configuration into object instance variables."""
        buf        = StringIO()
        trouble    = False
        self.exe_suffix = ''
        if sys.platform == 'win32':
            self.exe_suffix = '.exe'

        if 'graphviz' not in self.config.sections():
            msg = 'The <b>graphviz</b> section was not found in the trac configuration file.'
            buf = self.show_err(msg)
            trouble = True
        else:
            # check for the cache_dir entry
            if not self.config.parser.has_option('graphviz', 'cache_dir'):
                msg = 'The <b>graphviz</b> section is missing the <b>cache_dir</b> field.'
                buf = self.show_err(msg)
                trouble = True
            else:
                self.cache_dir = self.config.get('graphviz', 'cache_dir')
                if not os.path.exists(self.cache_dir):
                    msg = 'The <b>cache_dir</b> is set to <b>%s</b> but that path does not exist.' % self.cache_dir
                    buf = self.show_err(msg)
                    trouble = True
                self.log.debug('self.cache_dir: %s' % self.cache_dir)

            # check for the cmd_path entry
            if not self.config.parser.has_option('graphviz', 'cmd_path'):
                msg = 'The <b>graphviz</b> section is missing the <b>cmd_path</b> field.'
                buf = self.show_err(msg)
                trouble = True
            else:
                self.cmd_path = self.config.get('graphviz', 'cmd_path')
                if not os.path.exists(self.cmd_path):
                    msg = 'The <b>cmd_path</b> is set to <b>%s</b> but that path does not exist.' % self.cmd_path
                    buf = self.show_err(msg)
                    trouble = True

                for name in GraphvizMacro.processors:
                    if not os.path.exists(os.path.join(self.cmd_path, name) + self.exe_suffix):
                        msg = 'The <b>%s</b> program was not found in the <b>%s</b> directory.' % (name, self.cmd_path)
                        buf = self.show_err(msg)
                        trouble = True

                self.log.debug('self.cmd_path: %s' % self.cmd_path)

            # check for the prefix_url entry
            if not self.config.parser.has_option('graphviz', 'prefix_url'):
                msg = 'The <b>graphviz</b> section is missing the <b>prefix_url</b> field.'
                buf = self.show_err(msg)
                trouble = True
            else:
                self.prefix_url = self.config.get('graphviz', 'prefix_url')
                self.log.debug('self.prefix_url: %s' % self.prefix_url)


            #Get optional configuration parameters from trac.ini.

            # check for the default output format - out_format
            if self.config.parser.has_option('graphviz', 'out_format'):
                self.out_format = self.config.get('graphviz', 'out_format')
            else:
                self.out_format = GraphvizMacro.formats[0]
            self.log.debug('self.out_format: %s' % self.out_format)

            # check for the default processor - processor
            if self.config.parser.has_option('graphviz', 'processor'):
                self.processor = self.config.get('graphviz', 'processor')
            else:
                self.processor = GraphvizMacro.processors[0]
            self.log.debug('self.processor: %s' % self.processor)

            # check if png anti aliasing should be done - png_antialias
            if self.config.parser.has_option('graphviz', 'png_antialias'):
                self.png_anti_alias = True
            else:
                self.png_anti_alias = False
            self.log.debug('self.png_anti_alias: %s' % self.png_anti_alias)

            self.rsvg_path = '/usr/bin/rsvg'
            if self.png_anti_alias == True:
                if self.config.parser.has_option('graphviz', 'rsvg_path'):
                    self.rsvg_path = self.config.get('graphviz', 'rsvg_path')

                if not os.path.exists(self.rsvg_path):
                    err = 'The rsvg program is set to <b>%s</b> but that path does not exist.' % self.rsvg_path
                    buf = self.show_err(msg)
                    trouble = True
            self.log.debug('self.rsvg_path: %s' % self.rsvg_path)

            # get default graph/node/edge attributes
            self.processor_options = ''
            default_attributes = [ o for o in self.config.options('graphviz') if o[0].startswith('default_') ]
            if default_attributes:
               graph_attributes   = [ o for o in default_attributes if o[0].startswith('default_graph_') ]
               node_attributes    = [ o for o in default_attributes if o[0].startswith('default_node_') ]
               edge_attributes    = [ o for o in default_attributes if o[0].startswith('default_edge_') ]
               if graph_attributes:
                   self.processor_options += " ".join([ "-G" + o[0].replace('default_graph_', '') + "=" + o[1] for o in graph_attributes]) + " "
               if node_attributes:
                   self.processor_options += " ".join([ "-N" + o[0].replace('default_node_', '') + "=" + o[1] for o in node_attributes]) + " "
               if edge_attributes:
                   self.processor_options += " ".join([ "-E" + o[0].replace('default_edge_', '') + "=" + o[1] for o in edge_attributes])


            # check if we should run the cache manager
            if self.config.parser.has_option('graphviz', 'cache_manager'):
                self.cache_manager = True

                self.cache_max_size  = int(self.config.get('graphviz', 'cache_max_size'))
                self.cache_min_size  = int(self.config.get('graphviz', 'cache_min_size'))
                self.cache_max_count = int(self.config.get('graphviz', 'cache_max_count'))
                self.cache_min_count = int(self.config.get('graphviz', 'cache_min_count'))

                self.log.debug('self.cache_max_count: %d' % self.cache_max_count)
                self.log.debug('self.cache_min_count: %d' % self.cache_min_count)
                self.log.debug('self.cache_max_size: %d'  % self.cache_max_size)
                self.log.debug('self.cache_min_size: %d'  % self.cache_min_size)

            else:
                self.cache_manager = False

            # is there a graphviz default DPI setting?
            if self.config.parser.has_option('graphviz', 'default_graph_dpi'):
                self.dpi = int(self.config.get('graphviz', 'default_graph_dpi'))
            else:
                self.dpi = 96 # graphviz default

        return trouble, buf


    def launch(self, cmd, input):
        """Launch a process (cmd), and returns exitcode, stdout + stderr"""
	p_in, p_out, p_err = os.popen3(cmd)
        if input:
            p_in.writelines(input)
        p_in.close()
        out = p_out.read()
        err = p_err.read()
        return out, err


    def show_err(self, msg):
        """Display msg in an error box, using Trac style."""
        buf = StringIO()
        buf.write('<div id="content" class="error"><div class="message"> \n\
                   <strong>Graphviz macro processor has detected an error. Please fix the problem before continuing.</strong> \n\
                   <pre>%s</pre> \n\
                   </div></div>' % msg)
        self.log.error(msg)
        return buf


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

        if self.cache_manager:

            # os.stat gives back a tuple with: st_mode(0), st_ino(1),
            # st_dev(2), st_nlink(3), st_uid(4), st_gid(5),
            # st_size(6), st_atime(7), st_mtime(8), st_ctime(9)

            entry_list = {}
            atime_list = {}
            size_list = {}
            count = 0
            size = 0

            for name in os.listdir(self.cache_dir):
                self.log.debug('clean_cache.entry: %s' % name)
                entry_list[name] = os.stat(os.path.join(self.cache_dir, name))

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
            if count > self.cache_max_count or size > self.cache_max_size:
                while len(atime_keys) and (self.cache_min_count < count or self.cache_min_size < size):
                    key = atime_keys.pop(0)
                    for file in atime_list[key]:
                        self.log.debug('clean_cache.unlink: %s' % file)
                        os.unlink(os.path.join(self.cache_dir, file))
                        count = count - 1
                        size = size - entry_list[file][6]
        else:
            self.log.debug('clean_cache: cache_manager not set')
