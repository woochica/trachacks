"""

Copyright (c) 2010 Andrey Sergievskiy. All rights reserved.

Module documentation goes here.

"""



__revision__  = '$LastChangedRevision$'
__id__        = '$Id$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'
__version__   = '0.0.1'


import inspect
import locale
import os
import re
import sha
import subprocess
import sys

from genshi.builder import Element, tag
from genshi.core import Markup

from trac.config import BoolOption, IntOption, Option
from trac.core import *
from trac.mimeview.api import Context, IHTMLPreviewRenderer, MIME_MAP
from trac.util import escape
from trac.util.text import to_unicode
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import extract_link


class Metapost(Component):
	"""
	MetaPost (http://trac-hacks.org/wiki/MetaPostPlugin) provides
	a plugin for Trac to render MetaPost (http://foundry.supelec.fr/gf/project/metapost/)
	drawings within a Trac wiki page.
	"""
	implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)

	# Available formats and processors, default first (dot/png)
	Bitmap_Formats = ['png', 'jpeg', 'jpg', 'gif']
	Vector_Formats = ['svg', 'svgz']
	Formats = Bitmap_Formats + Vector_Formats 
	Cmd_Paths = {
		'linux2':	['/usr/bin', '/usr/local/bin', ],
#		'win32':	['c:\\Program Files\\MetaPost\\bin', ],
#		'freebsd6':	['/usr/local/bin', ],
#		'freebsd5':	['/usr/local/bin', ],
#		'darwin':	['/opt/local/bin', '/sw/bin',],
	}

	# Note: the following options named "..._option" are those which need
	#       some additional processing, see `_load_config()` below.

	DEFAULT_CACHE_DIR = '/tmp'

	cache_dir_option = Option("metapost", "cache_dir", DEFAULT_CACHE_DIR,
		"""The directory that will be used to cache the generated images.
		Note that if different than the default (`%s`), this directory must
		exist.
		If not given as an absolute path, the path will be relative to 
		the Trac environment's directory.
		""" % DEFAULT_CACHE_DIR)

	encoding = Option("metapost", "encoding", 'utf-8',
		"""The encoding which should be used for communicating with
		MetaPost.
		""")

	cmd_path = Option("metapost", "cmd_path", '',
		r"""Full path to the directory where the metapost
		programs are located. If not specified, the
		default is `/usr/bin` on Linux.
		""")

	out_format = Option("metapost", "out_format", Formats[0],
		"""Graph output format. Valid formats are: png, jpg,
		svg, svgz, gif. If not specified, the default is
		png. This setting can be overrided on a per-graph
		basis.
		""")

	cache_manager = BoolOption("metapost", "cache_manager", False,
		"""If this entry exists and set to true in the configuration file,
		then the cache management logic will be invoked
		and the cache_max_size, cache_min_size,
		cache_max_count and cache_min_count must be
		defined.
		""")

	cache_max_size = IntOption("metapost", "cache_max_size", 1024*1024*10,
		"""The maximum size in bytes that the cache should
		consume. This is the high watermark for disk space
		used.
		""")

	cache_min_size = IntOption("metapost", "cache_min_size", 1024*1024*5,
		"""When cleaning out the cache, remove files until
		this size in bytes is used by the cache. This is
		the low watermark for disk space used.
		""")

	cache_max_count = IntOption("metapost", "cache_max_count", 2000,
		"""The maximum number of files that the cache should
		contain. This is the high watermark for the
		directory entry count.
		""")

	cache_min_count = IntOption("metapost", "cache_min_count", 1500,
		"""The minimum number of files that the cache should
		contain. This is the low watermark for the
		directory entry count.
		""")


	def __init__(self):
		self.log.info('version: %s - id: %s'	% (__version__, str(__id__)))
		self.log.info('formats: %s'		% str(Metapost.Formats))


	# IHTMLPreviewRenderer methods

	MIME_TYPES = ('application/metapost')

	def get_quality_ratio(self, mimetype):
		if mimetype in self.MIME_TYPES:
			return 2
		return 0

	def render(self, context, mimetype, content, filename=None, url=None):
		ext = filename.split('.')[1]
		name = ext == 'metapost' and 'metapost' or 'metapost.%s' % ext
		text = hasattr(content, 'read') and content.read() or content
		return self.expand_macro(context, name, text)


	# IRequestHandler methods

	def match_request(self, req):
		return req.path_info.startswith('/metapost')

	def process_request(self, req):
		# check and load the configuration
		errmsg = self._load_config()
		if errmsg:
			return self._error_div(errmsg)

		pieces = [item for item in req.path_info.split('/metapost') if item]

		if pieces:
			pieces = [item for item in pieces[0].split('/') if item]

			if pieces:
				name = pieces[0]
				img_path = os.path.join(self.cache_dir, name)
				return req.send_file(img_path)

	# IWikiMacroProvider methods

	def get_macros(self):
		"""Return an iterable that provides the names of the provided macros."""
		self._load_config()
		for f in ['/' + f for f in Metapost.Formats] + ['']:
			yield 'metapost%s' % (f)


	def get_macro_description(self, name):
		"""
		Return a plain text description of the macro with the
		specified name. Only return a description for the base
		metapost macro. All the other variants (metapost/png,
		metapost/svg, etc.) will have no description. This will
		cleanup the WikiMacros page a bit.
		"""
		if name == 'metapost':
			return inspect.getdoc(Metapost)
		else:
			return None


	def expand_macro(self, formatter_or_context, name, content):
		"""Return the HTML output of the macro.

		:param formatter_or_context: a Formatter when called as a macro,
			a Context when called by `MetapostPlugin.render`

		:param name: Wiki macro command that resulted in this method being
			called. In this case, it should be 'metapost'
			by an output
			format, as following: metapost/<format>

			Valid output formats are: jpg, png, gif, svg and svgz.
			The default is the value specified in the out_format
			configuration parameter. If out_format is not specified
			in the configuration, then the default is png.

			examples:	metapost/png	-> png
					metapost/jpeg	-> jpeg
					metapost/jpg	-> jpg
					metapost	-> png
					metapost/svg	-> svg

		:param content: The text the user entered for the macro to process.
		"""

		# check and load the configuration
		errmsg = self._load_config()
		if errmsg:
			return self._error_div(errmsg)

		out_format = self.out_format

		# first try with the RegExp engine
		try: 
			m = re.match('metapost\/?([a-z]*)', name)
			(out_format) = m.group(1, 2)

		# or use the string.split method
		except:
			(s_sp) = (name.split('/'))
			if len(s_sp) > 1:
				out_format = s_sp[1]
            
		# assign default values, if instance ones are empty
		if not out_format:
			out_format = self.out_format

		if out_format not in Metapost.Formats:
			self.log.error('render_macro: requested format (%s) not found.' % out_format)
			return self._error_div(
				tag.p(_("Metapost macro processor error: requested format (%(fmt)s) not valid.",
					fmt=out_format)))

		encoded_content = content.encode(self.encoding)
		sha_key  = sha.new(encoded_content).hexdigest()

		mpost_name = '%s.%s' % (sha_key, 'mp')
		mpost_path = os.path.join(self.cache_dir, mpost_name)

		img_name = '%s.%s' % (sha_key, out_format)
		img_path = os.path.join(self.cache_dir, img_name)

		# Create image if not in cache
		if not os.path.exists(img_path):
			self._clean_cache()

			f = open(mpost_path, 'w+')
			f.write(encoded_content)
			f.close()

			os.system('cd %s ; mpost %s' % (self.cache_dir, mpost_name))
			os.system('cd %s ; mptopdf %s.%s' % (self.cache_dir, sha_key, '1'))

		if errmsg: 
			# there was a warning. Ideally we should be able to use
			# `add_warning` here, but that's not possible as the warnings
			# are already emitted at this point in the template processing
			return self._error_div(errmsg)

		# Generate HTML output
		img_url = formatter_or_context.href.metapost(img_name)
		# for SVG(z)
		if out_format in Metapost.Vector_Formats:
			os.system('cd %s ; pdf2svg %s-1.%s %s' % (self.cache_dir, sha_key, 'pdf', img_path))
			try: # try to get SVG dimensions
				f = open(img_path, 'r')
				svg = f.readlines(1024) # don't read all
				f.close()
				svg = "".join(svg).replace('\n', '')
				w = re.search('width="([0-9]+)(.*?)" ', svg)
				h = re.search('height="([0-9]+)(.*?)"', svg)
				(w_val, w_unit) = w.group(1,2)
				(h_val, h_unit) = h.group(1,2)
				# Graphviz seems to underestimate height/width for SVG images,
				# so we have to adjust them. 
				# The correction factor seems to be constant.
				w_val, h_val = [1.35 * float(x) for x in (w_val, h_val)]
				width = unicode(w_val) + w_unit
				height = unicode(h_val) + h_unit
			except ValueError:
				width = height = '100%'

			# insert SVG, IE compatibility
			return tag.object(
				tag.embed(src=img_url, type="image/svg+xml", 
					width=width, height=height),
					data=img_url, type="image/svg+xml", 
					width=width, height=height)

		else:
			os.system('cd %s ; pdftoppm %s-1.%s %s' % (self.cache_dir, sha_key, 'pdf', sha_key))
                        os.system('cd %s ; convert %s-1.%s %s' % (self.cache_dir, sha_key, 'ppm', img_name))
			return tag.img(src=img_url, alt=_("MetaPost image"))


	# Private methods

	def _load_config(self):
		"""Preprocess the metapost  trac.ini configuration."""

		# if 'metapost' not in self.config.sections():
		# ... so what? the defaults might be good enough

		# check for the cache_dir entry
		self.cache_dir = self.cache_dir_option
		if not self.cache_dir:
			return _("The [metapost] section is missing the cache_dir field.")

		if not os.path.isabs(self.cache_dir):
			self.cache_dir = os.path.join(self.env.path, self.cache_dir)

		if not os.path.exists(self.cache_dir):
			if self.cache_dir_option == self.DEFAULT_CACHE_DIR:
				os.mkdir(self.cache_dir)
			else:
				return _("The cache_dir '%(path)s' doesn't exist, "
					"please create it.", path=self.cache_dir)

		# Get optional configuration parameters from trac.ini.

		# check for the cmd_path entry and setup the various command paths
		cmd_paths = Metapost.Cmd_Paths.get(sys.platform, [])

		if self.cmd_path:
			if not os.path.exists(self.cmd_path):
				return _("The '[metapost] cmd_path' configuration entry "
					"is set to '%(path)s' but that path does not exist.", 
					path=self.cmd_path)
			cmd_paths = [self.cmd_path]

		if not cmd_paths:
			return _("The '[metapost] cmd_path' configuration entry "
				"is not set and there is no default for %(platform)s.",
				platform=sys.platform)

		self.cmds = {}

		# setup mimetypes to support the IHTMLPreviewRenderer interface
		if 'metapost' not in MIME_MAP:
			MIME_MAP['metapost'] = 'application/metapost'


	def _error_div(self, msg):
		"""Display msg in an error box, using Trac style."""
		if isinstance(msg, str):
			msg = to_unicode(msg)
		self.log.error(msg)
		if isinstance(msg, unicode):
			msg = tag.pre(escape(msg))
		return tag.div(
			tag.strong(_("Metapost macro processor has detected an error. "
				"Please fix the problem before continuing.")),
			msg, class_="system-message")


	def _clean_cache(self):
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

