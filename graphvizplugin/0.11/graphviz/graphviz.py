"""
$Id$
$HeadURL$

Copyright (c) 2005, 2006, 2008 Peter Kropf. All rights reserved.

Module documentation goes here.
"""



__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.7.2'


from StringIO import StringIO
import locale
import sha
import os
import sys
import re
import inspect
import subprocess

from trac.config import BoolOption, IntOption, Option
from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.mimeview.api import IHTMLPreviewRenderer, MIME_MAP
from trac.util import escape
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.wiki.formatter import wiki_to_oneliner
from trac.web.api import IRequestHandler


class Graphviz(Component):
    """
    Graphviz (http://trac-hacks.org/wiki/GraphvizPlugin) provides
    a plugin for Trac to render graphviz (http://www.graphviz.org/)
    drawings within a Trac wiki page.
    """
    implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)

    # Available formats and processors, default first (dot/png)
    Processors = ['dot', 'neato', 'twopi', 'circo', 'fdp']
    Bitmap_Formats = ['png', 'jpg', 'gif']
    Vector_Formats = ['svg', 'svgz']
    Formats = Bitmap_Formats + Vector_Formats 
    Cmd_Paths = {
        'linux2':   ['/usr/bin',
                     '/usr/local/bin',],
        
        'win32':    ['c:\\Program Files\\Graphviz\\bin',
                     'c:\\Program Files\\ATT\\Graphviz\\bin',
                     ],
        
        'freebsd6': ['/usr/local/bin',
                     ],
        
        'freebsd5': ['/usr/local/bin',
                     ],
        
        'darwin':   ['/opt/local/bin',
                     '/sw/bin',],
        
        }

    # Note: the following options named "..._option" are those which need
    #       some additional processing, see `_load_config()` below.


    cache_dir_option = Option("graphviz", "cache_dir", "gvcache",
            """The directory that will be used to cache the generated images
            (note that the directory must exist).
            If not given as an absolute path, the path will be relative to 
            the Trac environment's directory.
            """)

    encoding = Option("graphviz", "encoding", 'utf-8',
            """The encoding which should be used for communicating with
            Graphviz (should match -Gcharset if given).
            """)

    cmd_path = Option("graphviz", "cmd_path", '',
            r"""Full path to the directory where the graphviz
            programs are located. If not specified, the
            default is /usr/bin on Linux, c:\Program
            Files\ATT\Graphviz\bin on Windows and
            /usr/local/bin on FreeBSD 6.
            """)

    out_format = Option("graphviz", "out_format", Formats[0],
            """Graph output format. Valid formats are: png, jpg,
            svg, svgz, gif. If not specified, the default is
            png. This setting can be overrided on a per-graph
            basis.
            """)

    processor = Option("graphviz", "processor", Processors[0],
            """Graphviz default processor. Valid processors
            are: dot, neato, twopi, fdp, circo. If not
            specified, the default is dot. This setting can
            be overrided on a per-graph basis.

            GraphvizMacro will verify that the default
            processor is installed and will not work if it
            is missing. All other processors are optional.
            If any of the other processors are missing, a
            warning message will be sent to the trac log and
            GraphvizMacro will continue to work.
            """)

    png_anti_alias = BoolOption("graphviz", "png_antialias", False,
            """If this entry exists in the configuration file,
            then PNG outputs will be antialiased.
            Note that this requires `rsvg` to be installed.
            """)

    rsvg_path_option = Option("graphviz", "rsvg_path", "",
            """Full path to where the rsvg binary can be found.
            The default is cmd_path + rsvg.
            """)

    cache_manager = BoolOption("graphviz", "cache_manager", False,
            """If this entry exists and set to true in the configuration file,
            then the cache management logic will be invoked
            and the cache_max_size, cache_min_size,
            cache_max_count and cache_min_count must be
            defined.
            """)

    cache_max_size = IntOption("graphviz", "cache_max_size", 1024*1024*10,
            """The maximum size in bytes that the cache should
            consume. This is the high watermark for disk space
            used.
            """)

    cache_min_size = IntOption("graphviz", "cache_min_size", 1024*1024*5,
            """When cleaning out the cache, remove files until
            this size in bytes is used by the cache. This is
            the low watermark for disk space used.
            """)

    cache_max_count = IntOption("graphviz", "cache_max_count", 2000,
            """The maximum number of files that the cache should
            contain. This is the high watermark for the
            directory entry count.
            """)

    cache_min_count = IntOption("graphviz", "cache_minax_count", 1500,
            """The maximum number of files that the cache should
            contain. This is the high watermark for the
            directory entry count.
            """)

    dpi = IntOption('graphviz', 'default_graph_dpi', 96,
            """Default dpi setting for graphviz, used during SVG to PNG 
            rasterization.
            """)


    def __init__(self):
        self.log.info('version: %s - id: %s' % (__version__, str(__id__)))
        #self.log.info('processors: %s' % str(Graphviz.Processors))
        #self.log.info('formats: %s' % str(Graphviz.Formats))


    # IHTMLPreviewRenderer methods

    MIME_TYPES = ('application/graphviz')

    def get_quality_ratio(self, mimetype):
        self.log.error(mimetype)
        if mimetype in self.MIME_TYPES:
            return 2
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        ext = filename.split('.')[1]
        name = ext == 'graphviz' and 'graphviz' or 'graphviz.%s' % ext
        text = hasattr(content, 'read') and content.read() or content
        return self.render_macro(context, name, text)


    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/graphviz')


    def process_request(self, req):
        # check and load the configuration
        errmsg = self._load_config()
        if errmsg:
            return self._show_err(errmsg)

        pieces = [item for item in req.path_info.split('/graphviz') if item]

        if pieces:
            pieces = [item for item in pieces[0].split('/') if item]

            if pieces:
                name = pieces[0]
                img_path = os.path.join(self.cache_dir, name)
                return req.send_file(img_path)
        return

    # IWikiMacroProvider methods

    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        self._load_config()
        for p in ['.' + p for p in Graphviz.Processors] + ['']: 
            for f in ['/' + f for f in Graphviz.Formats] + ['']:
                yield 'graphviz%s%s' % (p, f)


    def get_macro_description(self, name):
        """
        Return a plain text description of the macro with the
        specified name. Only return a description for the base
        graphviz macro. All the other variants (graphviz/png,
        graphviz/svg, etc.) will have no description. This will
        cleanup the WikiMacros page a bit.
        """
        if name == 'graphviz':
            return inspect.getdoc(Graphviz)
        else:
            return None


    def expand_macro(self, formatter, name, content):
        """Return the HTML output of the macro.

        formatter - ?

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
        req = formatter.req

        # check and load the configuration
        errmsg = self._load_config()
        if errmsg:
            return self._show_err(errmsg)

        buf = StringIO()

        ## Extract processor and format from name
        processor = out_format = None

        # first try with the RegExp engine
        try: 
            m = re.match('graphviz\.?([a-z]*)\/?([a-z]*)', name)
            (processor, out_format) = m.group(1, 2)

        # or use the string.split method
        except:
            (d_sp, s_sp) = (name.split('.'), name.split('/'))
            if len(d_sp) > 1:
                s_sp = d_sp[1].split('/')
                if len(s_sp) > 1:
                    out_format = s_sp[1]
                processor = s_sp[0]
            elif len(s_sp) > 1:
                out_format = s_sp[1]
            
        # assign default values, if instance ones are empty
        if not out_format:
            out_format = self.out_format
        if not processor:
            processor = self.processor

        if processor in Graphviz.Processors:
            proc_cmd = self.cmds[processor]

        else:
            self.log.error('render_macro: requested processor (%s) not found.' %
                           processor)
            return self._show_err('requested processor (%s) not found.' % 
                                 processor)
           
        if out_format not in Graphviz.Formats:
            self.log.error('render_macro: requested format (%s) not found.' %
                           out_format)
            return self._show_err(
                    '<p>Graphviz macro processor '
                    'error: requested format (%s) not valid.</p>' % out_format)

        encoded_cmd = (processor + unicode(self.processor_options)) \
                .encode(self.encoding)
        encoded_content = content.encode(self.encoding)
        sha_key  = sha.new(encoded_cmd + encoded_content).hexdigest()
        img_name = '%s.%s.%s' % (sha_key, processor, out_format)
        # cache: hash.<dot>.<png>
        img_path = os.path.join(self.cache_dir, img_name)
        map_name = '%s.%s.map' % (sha_key, processor)
        # cache: hash.<dot>.map
        map_path = os.path.join(self.cache_dir, map_name)

        # Check for URL="" presence in graph code
        URL_in_graph = 'URL=' in content

        # Create image if not in cache
        if not os.path.exists(img_path):
            self.clean_cache()

            if URL_in_graph: # translate wiki TracLinks in URL
                content = self._expand_wiki_links(formatter, out_format, 
                                                  content)

            # Antialias PNGs with rsvg, if requested
            if out_format == 'png' and self.png_anti_alias == True:
                # 1. SVG output
                errmsg = self._launch(encoded_content, proc_cmd, '-Tsvg', 
                                      '-o%s.svg' % img_path,
                                      *self.processor_options)
                if errmsg:
                    return self._show_err(errmsg)

                # 2. SVG to PNG rasterization
                errmsg = self._launch(None, self.rsvg_path, 
                                      '--dpi-x=%d' % self.dpi,
                                      '--dpi-y=%d' % self.dpi,
                                      '%s.svg' % img_path, img_path)
                if errmsg:
                    return self._show_err(errmsg)
            
            else: # Render other image formats
                errmsg = self._launch(encoded_content, proc_cmd, 
                                      '-T%s' % out_format,
                                      '-o%s' % img_path, 
                                      *self.processor_options)
                if errmsg:
                    return self._show_err(errmsg)

            # Generate a map file for binary formats
            if URL_in_graph and out_format in Graphviz.Bitmap_Formats:

                # Create the map if not in cache
                if not os.path.exists(map_path):
                    errmsg = self._launch(encoded_content, proc_cmd, '-Tcmap',
                                          '-o%s' % map_path,
                                          *self.processor_options)
                    if errmsg:
                        return self._show_err(errmsg)

        # Generate HTML output
        # for SVG(z)
        if out_format in Graphviz.Vector_Formats:
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
                # so we have to adjust them. 
                # The correction factor seems to be constant.
                [w_val, h_val] = [ 1.35 * x for x in (int(w_val), int(h_val))]
                dimensions = ('width="%(w_val)s%(w_unit)s" '
                              'height="%(h_val)s%(h_unit)s"' % locals())

            except:
                dimensions = 'width="100%" height="100%"'

            # insert SVG, IE compatibility
            buf.write('<object data="%s/graphviz/%s" type="image/svg+xml" %s><embed src="%s/graphviz/%s" type="image/svg+xml" %s></embed></object>' % (req.base_url, img_name, dimensions, req.base_url, img_name, dimensions))

        # for binary formats, add map
        elif URL_in_graph and os.path.exists(map_path):
            f = open(map_path, 'r')
            map = f.readlines()
            f.close()
            map = "".join(map).replace('\n', '')
            buf.write('<map id="%s" name="%s">%s</map>' % (sha_key, sha_key, map))
            buf.write('<img id="%s" src="%s/graphviz/%s" usemap="#%s" alt="GraphViz image"/>' % (sha_key, req.base_url, img_name, sha_key))

        else:
            buf.write('<img src="%s/graphviz/%s"/>' % (req.base_url, img_name))

        return buf.getvalue()


    # Private methods

    def _expand_wiki_links(self, formatter, out_format, content):
        """Expand TracLinks that follow all URL= patterns."""
        def _expand(match):
            wiki_url = match.groups()[0] # TracLink ([1], source:file/, ...)
            html_url = wiki_to_oneliner(wiki_url, self.env, req=formatter.req)
            # <a href="http://someurl">...</a>

            href     = re.search('href="(.*?)"', html_url)   # http://someurl
            url      = href and href.groups()[0] or html_url
            if out_format == 'svg':
                format = 'URL="javascript:window.parent.location.href=\'%s\'"'
            else:
                format = 'URL="%s"'
            return format % url
        return re.sub(r'URL="(.*?)"', _expand, content)

    def _load_config(self):
        """Preprocess the graphviz trac.ini configuration."""

        # if 'graphviz' not in self.config.sections():
        # ... so what? the defaults might be good enough

        # check for the cache_dir entry
        self.cache_dir = self.cache_dir_option
        if not self.cache_dir:
            return _("The [graphviz] section is missing the cache_dir field.")

        if not os.path.isabs(self.cache_dir):
            self.cache_dir = os.path.join(self.env.path, self.cache_dir)

        if not os.path.exists(self.cache_dir):
            return _("The cache_dir '%(path)s' doesn't exist, "
                    "please create it.", path=self.cache_dir)

        # Get optional configuration parameters from trac.ini.

        # check for the cmd_path entry and setup the various command paths
        cmd_paths = Graphviz.Cmd_Paths.get(sys.platform, [])

        if self.cmd_path:
            if not os.path.exists(self.cmd_path):
                return _("The '[graphviz] cmd_path' configuration entry "
                         "is set to '%(path)s' but that path does not exist.", 
                         path=self.cmd_path)
            cmd_paths = [self.cmd_path]

        if not cmd_paths:
            return _("The '[graphviz] cmd_path' configuration entry "
                     "is not set and there is no default for %(platform)s.",
                     platform=sys.platform)

        self.cmds = {}
        pname = self._find_cmd(self.processor, cmd_paths)
        if not pname:
            return _("The default processor '%(proc)s' was not found "
                     "in '%(paths)s'.", proc=self.processor, paths=cmd_paths)

        for name in Graphviz.Processors:
            pname = self._find_cmd(name, cmd_paths)

            if not pname:
                self.log.warn('The %s program was not found. '
                              'The graphviz/%s macro will be disabled.' %
                              (pname, name))
                Graphviz.Processors.remove(name)

            self.cmds[name] = pname

        if self.png_anti_alias:
            self.rsvg_path = self.rsvg_path_option or \
                    self._find_cmd('rsvg', cmd_paths)
            
            if not os.path.exists(self.rsvg_path):
                return _("The rsvg program is set to '%(path)s' but that path "
                         "does not exist.", path=self.rsvg_path)

        # get default graph/node/edge attributes
        self.processor_options = []
        defaults = [opt for opt in self.config.options('graphviz') 
                    if opt[0].startswith('default_')]
        for name, value in defaults:
            for prefix, optkey in [
                    ('default_graph_', '-G'), 
                    ('default_node_', '-N'),
                    ('default_edge_', '-E')]:
                if name.startswith(prefix):
                    self.processor_options.append("%s%s=%s" % 
                            (optkey, name.replace(prefix,''), value))

        # setup mimetypes to support the IHTMLPreviewRenderer interface
        if 'graphviz' not in MIME_MAP:
            MIME_MAP['graphviz'] = 'application/graphviz'
        for processor in Graphviz.Processors:
            if processor not in MIME_MAP:
                MIME_MAP[processor] = 'application/graphviz'

    def _launch(self, encoded_input, *args):
        """Launch a process (cmd), and returns exitcode, stdout + stderr"""
        # Note: subprocess.Popen doesn't support unicode options arguments
        # (http://bugs.python.org/issue1759845) so we have to encode them.
        # Anyway, dot expects utf-8 or the encoding specified with -Gcharset.
        encoded_cmd = []
        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode(self.encoding, 'replace')
            encoded_cmd.append(arg)
        p = subprocess.Popen(encoded_cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if input:
            p.stdin.write(encoded_input)
        p.stdin.close()
        out = p.stdout.read()
        err = p.stderr.read()
        if out or err:
            return _("The command\n   %(cmd)s\n"
                     "failed with the the following output:\n"
                     "%(out)s\n%(err)s", cmd=unicode(args), out=out, err=err)

    def _show_err(self, msg):
        """Display msg in an error box, using Trac style."""
        buf = StringIO()
        buf.write('<div id="content" class="error"><div class="message"> \n\
                   <strong>Graphviz macro processor has detected an error. Please fix the problem before continuing.</strong> \n\
                   <pre>%s</pre> \n\
                   </div></div>' % escape(to_unicode(msg)))
        self.log.error(msg)
        return buf.getvalue()


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
                #self.log.debug('clean_cache.entry: %s' % name)
                entry_list[name] = os.stat(os.path.join(self.cache_dir, name))

                atime_list.setdefault(entry_list[name][7], []).append(name)
                count = count + 1

                size_list.setdefault(entry_list[name][6], []).append(name)
                size = size + entry_list[name][6]

            atime_keys = atime_list.keys()
            atime_keys.sort()

            #self.log.debug('clean_cache.atime_keys: %s' % atime_keys)
            #self.log.debug('clean_cache.count: %d' % count)
            #self.log.debug('clean_cache.size: %d' % size)
        
            # In the spirit of keeping the code fairly simple, the
            # clearing out of files from the cache directory may
            # result in the count dropping below cache_min_count if
            # multiple entries are have the same last access
            # time. Same for cache_min_size.
            if count > self.cache_max_count or size > self.cache_max_size:
                while atime_keys and (self.cache_min_count < count or  
                                      self.cache_min_size < size):
                    key = atime_keys.pop(0)
                    for file in atime_list[key]:
                        os.unlink(os.path.join(self.cache_dir, file))
                        count = count - 1
                        size = size - entry_list[file][6]

    def _find_cmd(self, cmd, paths):
        exe_suffix = ''
        if sys.platform == 'win32':
            exe_suffix = '.exe'

        pname = None
        for path in paths:
            p = os.path.join(path, cmd) + exe_suffix
            if os.path.exists(p):
                pname = p
                break

        return pname
