#
# Tracwikidoc plugin
# Shamelessly copied and butchered from tracperldoc.py
# I'm basically a dog at Python, so beware...
#
# Cosimo <cosimo@cpan.org>
#
# $Id: tracwikidoc.py 9864 2008-12-11 17:32:20Z cosimo $

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, shorten_line, to_unicode
from trac.wiki.api import IWikiSyntaxProvider, IWikiMacroProvider
from trac.search import ISearchSource
import inspect, os

try:
	from trac.util import Markup
except ImportError:
	def Markup(markup): return markup

import urllib
import re
import time
import sys
import os
import imp
import cgi
import stat
import StringIO
import popen2

try:
	import threading
except ImportError:
	import dummy_threading as threading

class WikidocDoc:
	def __init__(self):
		self.title = ''
		self.src_link = ''
		self.html = ''
		self.html_index = ''

class WikidocParser:
	""" Generate HTML from a wikidoc file or an index. """

	def __init__(self, env, repo):
		self.env = env

		self.urlroot = env.href.wikidoc() + '/'
		self.paths = env.config.get('wikidoc', 'wikidoc.paths').strip().split(':')
		self.repo_paths = env.config.get('wikidoc', 'svn.paths').strip().split(':')
		self.exts = ['.wikidoc','.pm', '.pl']

		self.svn = repo

		self.svn_lock = threading.Lock()

	def _inc_path(self, name):
		for path in self.paths:
			if path.endswith(name):
				return 1
		return 0

	def _list_sum(self, list):
		s = 0
		for i in list:
			s = s + i
		return s

	def index(self, module=None):
		self.svn_lock.acquire()
		doc = WikidocDoc()
		doc.title = 'Module Index'
		doc.html = '<p class="poderror">Internal Error</p>'
		try:
			doc.html = self._make_index(doc, module)
		finally:
			self.svn_lock.release()
		return doc

	def _make_index(self, doc, module=None):
		""" Generate a Wikidoc index. """

		if module == None:
			module = ''

		module = module.replace('/', '::').replace('.','')
		mpath = module.replace('::','/').rstrip('/')

		if len(mpath) > 0:
			doc.title = doc.title + ': ' + mpath

		mdirs = {}
		mfiles = {}

		for path in self.paths:
			top = os.path.join(path, mpath)
			for ext in self.exts:
				try:
					st = os.lstat(top + ext)
					if stat.S_ISREG(st.st_mode):
						mfiles[''] = top
				except os.error:
					pass
			try:
				names = os.listdir(top)
			except os.error:
				continue
			for name in names:
				try:
					st = os.lstat(os.path.join(top, name))
				except os.error:
					continue
				if stat.S_ISDIR(st.st_mode):
					if not self._inc_path(os.path.join(top, name)):
						mdirs[name] = top
				else:
					for ext in self.exts:
						if name.endswith(ext):
							mfiles[name[:-1*len(ext)]] = top

		rev = self.svn.get_youngest_rev()
		rev = self.svn.normalize_rev(rev)
		for path in self.repo_paths:
			top = '/'.join([path, mpath])

			# Get the module of the same name (if it exists)
			for ext in self.exts:
				if not self.svn.has_node(top + ext, rev): continue
				entry = self.svn.get_node(top + ext)
				if entry.isfile:
					href = self.env.href('browser') + top + ext
					label = top + ext
					mfiles[''] = '<a href="%s" class="podindex">source:%s</a>' % (href,label)

			if not self.svn.has_node(top, rev): continue 
			node = self.svn.get_node(top)
			# If its a file it won't have any entries
			for entry in node.get_entries():
				name = entry.get_name()
				href = self.env.href('browser') + '/'.join([top,name])
				label = '/'.join([top,name])
				if entry.isdir:
					mdirs[name] = '<a href="%s" class="podindex">source:%s</a>' % (href,label)
				elif entry.isfile:
					for ext in self.exts:
						if name.endswith(ext):
							mfiles[name[:-1*len(ext)]] = '<a href="%s" class="podindex">source:%s</a>' % (href,label)

		if len(mdirs) == 0 and len(mfiles) == 0:
			return '<p class="poderror">No matching modules found (perhaps the administrator needs to specify <tt>wikidoc.inc</tt> in <tt>trac.conf</tt>?).</p>'

		result = '<ul class="podindex">\n'

		names = mdirs.keys()
		names.sort()
		for name in names:
			path = mdirs[name]
			if name != '' and module != '':
				name = module + '::' + name
			url = self.urlroot + name + '*'
			name = name.replace('::','/') + '/'
			result = result + '<li class="podindexdir"><a href="%s">%s</a></li>\n' % (self.escape(url), name)

		names = mfiles.keys()
		names.sort()
		for name in names:
			path = mfiles[name]
			if name != '' and module != '':
				name = module + '::' + name
			elif name == '':
				name = module
			url = self.urlroot + name
			result = result + '<li class="podindexfile"><a href="%s">%s</a> <span class="podindexpath">[%s]</a></li>\n' % (self.escape(url), name, path)

		result = result + '</ul>\n'

		return result

	def document(self, module):
		self.svn_lock.acquire()
		doc = WikidocDoc()
		doc.title = module
		doc.html = '<p class="poderror">Internal Error</p>'
		try:
			doc.html = self._make_document(doc, module)
			doc.html_index = self._make_document_index(doc)
		finally:
			self.svn_lock.release()
		return doc
		
	def _open_file(self, filename):
		fh = None
                self.env.log.info('open_file:' + filename)
		if os.access(filename, os.R_OK):
                        stdout, stdin = popen2.popen2("wikidoc " + filename)
                        stdin.close()
                        fh = stdout.read()
		return fh

	def _open_svn(self, filename):
		fh = None
		rev = self.svn.get_youngest_rev()
		rev = self.svn.normalize_rev(rev)
                self.env.log.info('open_svn:' + filename)
		if self.svn.has_node(filename, rev):
			node = self.svn.get_node(filename)
			if node.isfile:
				fh = StringIO.StringIO(node.get_content().read())
		return fh

	def _make_document_index(self, doc):
		depth = 0
		result = ''
		for link in self.headings:
			(level,aname,label) = link
			while( depth < level ):
				result = result + '<ul class="podnav">\n'
				depth = depth + 1
			while( depth > level ):
				result = result + '</ul>\n'
				depth = depth - 1
			result = result + '<li class="podnav"><a href="#%s" class="podnav">%s</a></li>\n' % (aname, label)
		while( depth > 0 ):
			result = result + '</ul>\n'
			depth = depth - 1
		return result

	def _make_document(self, doc, module):
		""" Generate documentation for a Wiki module. """

		# Replace any dangerous characters
		self.module = module = module.replace('/', '::').replace('.','')
		# Translate the name to a filename
		modfile = module.replace('::','/')

		fh = None

		self.headings = []

		# Find the module in self.paths/repo_paths
		for ext in self.exts:
			for path in self.repo_paths:
				filename = path + '/' + modfile + ext
				fh = self._open_svn(filename)
				if fh != None:
					doc.src_link = self.env.href('browser') + filename
					break
			if fh != None: break
			for path in self.paths:
				fh = self._open_file(path + '/' + modfile + ext)
				if fh != None: break
			if fh != None: break

		if fh == None:
			return '<p class="poderror">Could not locate %s.</p>' % module

		result = ''

		allpod = inpod = inlist = fixed = 0
		self.indent = []
		self.itemformat = [];
		buffer = ''
		for line in fh:
			line = line[:-1]
			# Should we output some text?
			if buffer != '':
				# Output a paragraph of normal text
				# or A new pod directive, definitely output
				if (len(line) == 0 and fixed == 0) or (len(line) > 0 and line[0] == '='):
					buffer = buffer.rstrip()
					if len(self.indent) > 0:
						result = result + self.itemtext(buffer,fixed)
					else:
						result = result + self.podtext(buffer,fixed)
					buffer = ''
					fixed = 0
				# Otherwise we may output below
			if len(line) == 0:
				if fixed == 1 and buffer != '':
					buffer = buffer + '\n'
			elif line[:2] == '= ':
				result = result + self.head(line[2:], 1)
				inpod = 1
				self.indent = []
			elif line[:3] == '== ':
				result = result + self.head(line[3:], 2)
				inpod = 1
				self.indent = []
			elif line[:4] == '=== ':
				result = result + self.head(line[4:], 3)
				inpod = 1
				self.indent = []
			elif line[:2] == '* ':
				self.indent = [ 4 ]
				result = result + self.item(line[2:])
				inpod = 1
			elif line[:14] == '=begin wikidoc':
				inpod = 1
				self.indent = []
			elif line[:12] == '=end wikidoc':
				inpod = 0
				self.indent = []
			elif line[:7] == '__END__':
				allpod = 1
			elif inpod == 1 or allpod == 1:
				# Indented text, just add it to the buffer
				if line[0] == '\t' or line[0] == ' ':
					# Don't set fixed if this isn't the first line
					if buffer == '':
						fixed = 1
				# End of indented text, output it, buffer this line
				elif fixed == 1:
					buffer = buffer.rstrip()
					if len(self.indent) > 0:
						result = result + self.itemtext(buffer,fixed)
					else:
						result = result + self.podtext(buffer,fixed)
					buffer = ''
					fixed = 0	
				buffer = buffer + line + '\n'

		if buffer != '':
			result = result + self.podtext(buffer.rstrip(),fixed)
			buffer = ''

		# Make sure lists are closed
		while len(self.itemformat) > 0:
			result = result + self.back()

		return result

	def head(self, title, level):
		level = int(level) + 1
		aname = self.escape_relative(title)
		label = self.format(title)
		self.headings.append([level-1, aname, label])
		return '<h%d class="pod"><a name="%s">%s</a></h1>\n' % (level,aname,label)

	def over(self, indent):
		try:
			indent = int(indent)
		except ValueError:
			indent = 4
		self.indent.append(indent)
		return ''

	def back(self):
		if len(self.indent) > 0:
			self.indent.pop()
		if len(self.itemformat) > len(self.indent):
			type = self.itemformat.pop()
			if type == '*':
				return '</ul>'
			elif type == '#':
				return '</ol>'
			else:
				return ''
		else:
			return ''

	def item(self, title):
		result = ''
		# Has the doc called =over ?
		if len(self.indent) > 0:
			# Have we already determined the list format?
			if len(self.itemformat) < len(self.indent):
				# Unordered list
				if title == '*':
					self.itemformat.append('*')
					result = '<ul class="pod">\n'
				# Ordered list (numbered)
				elif title.isdigit():
					self.itemformat.append('#')
					# self.itemindex = title[:-1] # Unused, HTML counts for us
					result = '<ol class="pod">\n'
				# General items (but indented)
				else:
					self.itemformat.append('a')
		# Handle an =item if =over hasn't been called
		if len(self.indent) == 0 or self.itemformat[-1] == 'a':
			return '<div style="padding-left: %dem" class="poditem"><a name="%s">%s</a></div>\n' % (self._list_sum(self.indent[:-1]),self.escape_relative(title),self.format(title))
		else:
			return result

	def itemtext(self, text, fixed):
		if len(self.itemformat) == 0 or self.itemformat[-1] == 'a':
			return '<div style="padding-left: %dem">\n' % self._list_sum(self.indent) + self.podtext(text,fixed) + '</div>\n'
		elif self.itemformat[-1] == '*':
			return '<li class="poditem">' + self.format(text) + '</li>\n';
		elif self.itemformat[-1] == '#':
			return '<li class="poditem">' + self.format(text) + '</li>\n';

	def podtext(self,text,fixed):
		if text == '':
			return ''
		elif fixed == 1:
			return '<pre class="pod">' + self.escape(text) + '</pre>\n\n';
		else:
			return '<p class="pod">' + self.format(text) + '</p>\n\n'

	def format(self,text):
		""" Expand WIKIDOC formatting/links to HTML. """

		re_code = re.compile('{[^}]+}')
		re_bold = re.compile("'''[^']+'''")

		result = ''

		while text != '':

			match = re_code.search(text)

			if match == None:
				result = result + self.escape(text)
				text = ''
			elif match.start:
				result = result + self.escape(text[:match.start()])
				text = text[match.end():]
				result = result + self.format_code(match.group()[1:-1])
			else:
				sys.stderr.write('This should not happen')
				sys.exit()

		text = result
		result = ''

		while text != '':

			match = re_bold.search(text)

			if match == None:
				result = result + text
				text = ''
			elif match.start:
				result = result + text[:match.start()]
				text = text[match.end():]
				result = result + self.format_bold(match.group()[3:-3])
			else:
				sys.stderr.write('This should not happen')
				sys.exit()

		return result

	def format_bold(self, text):
		result = '<b>'
		result += text
		result += '</b>'
		return result

	def format_code(self, text):
		result = '<code>'
		result += text
		result += '</code>'
		return result

	# Handle new-style multi-bracketed C<< ... >>
	def format_new(self,text,tag):
		end_tag = ' ' + '>' * (len(tag)-2)
		m = re.compile(end_tag).search(text)
		r = ''
		if m != None:
			r = text[m.end():]
			text = text[:m.start()]
		else:
			return (r,text)
		return (self.format_tag(text,tag[0]), r)

	# Handle old-style single-bracket E<...>
	def format_old(self,text,tag):
		c = 1
		for i in range(0,len(text)):
			if text[i] == '>':
				c = c - 1
			elif text[i] == '<':
				c = c + 1
			if c == 0:
				break
		r = text[i+1:]
		text = text[:i]
		return (self.format_tag(text,tag[0]), r)
		

	def format_tag(self,text,tag):
		if tag == 'E':
			if text == 'lt':
				return '<'
			elif text == 'gt':
				return '>'
			else:
				return '&' + text + ';'
		re_scheme = re.compile('(http|https|ftp|mailto|nntp):[^:]')
		if tag == 'L':
			# URL
			if re_scheme.match(text):
				text = self.escape(text)
				return '<a href="%s" class="pod">%s</a>' % (text,text)
			url = self.urlroot

			# Get the label
			words = text.split('|',2)
			label = None
			if len(words) == 2:
				label = words[0]
				text = words[1]
			else:
				label = text = words[0]
			label = self.escape(label.replace('"','')).replace('/','#')

			# Sort out relative urls
			if text[0] == '/' or text[0] == '"' or (text.find('/') == -1 and text.find(' ') > -1):
				url = '#' + self.escape_relative(text)
			elif text.find('/') > -1:
				words = text.split('/',2)
				if len(words) == 2:
					url = url + words[0] + '#' + self.escape_relative(words[1])
					text = '/' + words[1]
			else:
				url = url + text
			
			# Relative
			return '<a href="%s" class="pod">%s</a>' % (url,label)

		text = self.format(text)
		if tag == 'I':
			return '<i class="pod">' + text + '</i>'
		elif tag == 'C' or tag == 'F':
			return '<tt class="pod">' + text + '</tt>'
		elif tag == 'B':
			return '<b class="pod">' + text + '</b>'
		#elif tag == 'S': # Not supported
		#	return text
		#elif tag == 'X': # Not supported
		#	return text
		else:
			return text

	def escape(self,text):
		return cgi.escape(text.replace('Z<>',''))

	def escape_relative(self,text):
		return cgi.escape(text.strip().replace('"','').replace('/','').replace('#','')).replace(' ','+')

class WikiDoc(Component):
	""" Allow browsing of Python documentation through Trac. """

	implements(INavigationContributor, ITemplateProvider, IRequestHandler)

	def __init__(self):
		self.permission = self.config.get('wikidoc', 'view.permission')
		if not self.permission:
			self.permission = 'BROWSER_VIEW'

	def _link_components(self, path):
		if not path: return []
		links = []
		sofar = []
		if path[-1] == '*':
			path = path[:-1]
		for mod in path.split('::'):
			sofar.append(mod)
			links.append('<a href="%s*" class="pod">%s</a>' % \
				(self.env.href.wikidoc('::'.join(sofar)), mod))
		return links
 
	def generate_help(self, target, repo, inline=False, visibility=''):
		"""Show documentation for named `target`.

		If `inline` is set, no header will be generated.
		For the `visibility` argument, see `PyDocMacro`.
		"""
		parser = WikidocParser(self.env, repo)
		html = ''

		if target == '':
			doc = parser.index(target)
		elif target[-1] == '*':
			doc = parser.index(target[:-1])
		else:
			doc = parser.document(target)

		if not target or target[-1] == '*':
			if not inline:
				html = '<h1 class="pod">%s</h1>\n\n' % doc.title
		else:
			if not inline:
				html = '<h1 class="pod">%s</h1>\n\n' % doc.title
		if doc.src_link != '':
			src = ' [<a href="%s" class="podindex">%s</a>]' % (doc.src_link, doc.src_link)
		else:
			src = ''
		links = self._link_components(target)
		if len(links) == 0:
			html = html + '<p class="podpath">%s %s</p>\n' % ('@INC', src)
		else:
			links.insert(0,'<a href="%s">@INC</a>' % self.env.href.wikidoc())
			links[-1] = target.split('::')[-1] # Unlink it
			html = html + '<p class="podpath">%s %s</p>\n' % ('::'.join(links), src)
		#doc = doc + '<pre>%s</pre>\n' % '\n'.join(parser.paths)

		return to_unicode(html) + to_unicode(doc.html_index) + to_unicode(doc.html)

	# INavigationContributor methods
    
	def get_active_navigation_item(self, req):
		return 'wikidoc'
                
	def get_navigation_items(self, req):
		if req.perm.has_permission(self.permission):
			yield 'mainnav', 'wikidoc', Markup('<a href="%s">WikiDoc</a>' \
										% escape(self.env.href.wikidoc()))

	# IRequestHandler methods
    
	def match_request(self, req):
		return req.path_info.startswith('/wikidoc')

	def process_request(self, req):
		req.perm.assert_permission(self.permission)

		repo = self.env.get_repository(req.authname)

		add_stylesheet(req, 'wikidoc/css/wikidoc.css')
		target = req.path_info[9:]
		req.hdf['trac.href.wikidoc'] = self.env.href.wikidoc()
		req.hdf['wikidoc.trail'] = [Markup(x) for x in 
									self._link_components(target)[:-1]]
		req.hdf['wikidoc.trail_last'] = target.split('::')[-1]
		req.hdf['wikidoc.content'] = Markup(self.generate_help(target, repo))
		req.hdf['title'] = target
		return 'wikidoc.cs', None

	# ITemplateProvider methods
    
	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'templates')]

	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [('wikidoc', resource_filename(__name__, 'htdocs'))]


class WikiDocWiki(Component):
    """Provide wiki wikidoc:object link syntax."""

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('wikidoc', self._wikidoc_formatter)

    def _wikidoc_formatter(self, formatter, ns, object, label):
        object = urllib.unquote(object)
        label = urllib.unquote(label)
        if not object or object == '*':
            return '<a class="wiki" href="%s">%s</a>' % \
                   (formatter.href.wikidoc(), label)
        else:
			return '<a class="wiki" href="%s">%s</a>' % \
				(formatter.href.wikidoc(object), label)
            

#class WikiDocMacro(Component):
#	"""Show the Wiki documentation for the given `target`.

#	"""

#	implements(IWikiMacroProvider)

	# IWikiMacroProvider methods

#	def get_macros(self):
#		yield 'wikidoc'

#	def get_macro_description(self, name):
#		return self.__doc__
    
#	def render_macro(self, req, name, content):
#		args = content.split(',')
#		target = args and args.pop(0)
#		visibility = args and args.pop(0).strip() or ''
#		add_stylesheet(req, 'wikidoc/css/wikidoc.css')
#		return WikiDoc(self.env).generate_help(target, inline=True,
#												visibility=visibility)


#class WikiDocSearch(Component):
#	""" Provide searching of Wiki documentation [TODO]. """
#
#	implements(ISearchSource)
#
	# ISearchSource methods

#	def get_search_filters(self, req):
#		yield ('wikidoc', 'Wiki Documentation', 0)

#	def get_search_results(self, req, query, filters):
#		return []

