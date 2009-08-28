__version__   = '0.1'
__id__        = '$Id$'
__revision__  = '$LastChangedRevision$'
__headurl__   = '$HeadURL$'
__docformat__ = 'restructuredtext'

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

__all__ = ['Mscgen']

# implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler) 

class Mscgen(Component):
	"""
	Mscgen (http://trac-hacks.org/wiki/MscgenPlugin) provides
	a plugin for Trac to render mscgen (http://www.mcternan.me.uk/mscgen/)
	message sequence chart diagrams within a Trac wiki page.
	"""

	implements(IWikiMacroProvider, IHTMLPreviewRenderer, IRequestHandler)

	def __init__(self):
		self.cache_dir = "%s/mscgen" % (self.env.path)
		self.proc_path = "/usr/local/bin/mscgen"
		self.proc_opts = ""
		self.log.info('version: %s - id: %s' % (__version__, str(__id__)))

	def errmsg(self,msg):
		self.log.error(msg)
		return tag.div(
				tag.strong(_("mscgen internal error")),
				msg, class_="system-message")

	def cfg_load(self):
		return False 

	def launch(self, proc_cmd, encoded_input, *args):
		"""Launch a process (cmd), and returns exitcode, stdout + stderr"""
		# Note: subprocess.Popen doesn't support unicode options arguments
		# (http://bugs.python.org/issue1759845) so we have to encode them.
		# Anyway, dot expects utf-8 or the encoding specified with -Gcharset.
		encoded_cmd = proc_cmd
		proc = subprocess.Popen(encoded_cmd, stdin=subprocess.PIPE,
			stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if encoded_input:
			proc.stdin.write(encoded_input)
		proc.stdin.close()
		out = proc.stdout.read()
		err = proc.stderr.read()
		failure = proc.wait() != 0
		if failure or err or out:
			return (failure, tag.div(tag.br(), _("The command:"), 
				tag.pre(repr(' '.join(encoded_cmd))), 
					       (_("succeeded but emitted the following output:"),
						_("failed with the following output:"))[failure],
					       out and tag.pre(out), 
					       err and tag.pre(err), class_="system-message"))
		else:
			return (False, None)

	# IWikiMacroProvider interface
	def get_macros(self):
		self.log.info('get_macros')
		yield 'mscgen'
	
	def get_macro_description(self,name):
		self.log.info('get_macro_desc')
		return "Provide a mscgen diagrams parser"
	
	def expand_macro(self, formatter, name, content):
		self.log.info('expand_macro')
		sha_key  = sha.new(content).hexdigest()
		img_name = "%s.png" % (sha_key)
		img_path = os.path.join(self.cache_dir, img_name)

                cmd = [self.proc_path, '-T', 'png', '-o', img_path]
		self.log.info("cmd=%s" % (' '.join(cmd)))
                out, err = self.launch(cmd, content)
		
		if out or err:
			msg = 'The command\n   %s\nfailed with the the following output:\n%s\n%s' % (cmd, out, err) 
			return err

		img_url = formatter.href.mscgen(img_name)
		return tag.img(src=img_url, alt=_("mscgen image"))

	# IHTMLPreviewRenderer interface

	def get_quality_ratio(self, mimetype):
		return 0

	def render(context, mimetype, content, filename=None, url=None):
		self.log.info('render')
		ext = filename.split('.')[1]
		name = ext == 'mscgen' and 'mscgen' or 'mscgen.%s' % ext
		text = hasattr(content, 'read') and content.read() or content
		return self.expand_macro(context, name, text)


	# IRequestHandler interface

	def match_request(self, req):
		self.log.info('match_reguest %s ' % (req.path_info))
		return req.path_info.startswith('/mscgen')

	def process_request(self, req):
		self.log.info('process_reguest %s ' % (req.path_info))
		# check and load the configuration
		errmsg = self.cfg_load()
		if errmsg:
			return self.errmsg(errmsg)

		pieces = [item for item in req.path_info.split('/mscgen') if item]

		if pieces:
			pieces = [item for item in pieces[0].split('/') if item]

			if pieces:
				name = pieces[0]
				img_path = os.path.join(self.cache_dir, name)
				return req.send_file(img_path)
