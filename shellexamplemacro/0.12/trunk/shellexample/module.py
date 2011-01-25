from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
#from trac.wiki.api import IWikiMacroProvider
from trac.web.main import IRequestHandler
from trac.util import escape
from genshi.core import Markup
from trac.wiki.macros import WikiMacroBase
import re

__all__ = ['ShellExample']

class ShellExample(WikiMacroBase):
	implements(IRequestHandler, ITemplateProvider)
	revision = "$Rev$"
	url = "$URL$"

	regex_crlf = re.compile('''(\r\n|\r|\n)''')
	patt_printable =  '[*-_./!@~a-zA-Z0-9]'
	patt_userreplacement =  '\{%s+\}' % (patt_printable)
	patt_singlequote =  "'.*?(?<!\\\\)'"
	patt_doublequote =  '".*?(?<!\\\\)"'
	patt_cmdoption =  '(?<=\s)-{1,2}%s+=?' % (patt_printable)
	patt_continuation =  '\\\\\\n'
	patt_wrd = '.*?'
	patt_pth = '[-~_ /a-zA-Z0-9]+'
	patt_userhost =  '([-._a-zA-Z0-9]+)?@?([-._a-zA-Z0-9]+)?'
	patt_input = '\s*%s|\s*%s|\s*%s|\s*%s|%s' % (patt_userreplacement, 
			patt_singlequote, patt_doublequote, patt_continuation, patt_wrd)
	regexp = re.compile(
			('^(?P<path>[\[({]?(%s( %s)?)[\])}:]?)?(?P<cli>[#$] )(?P<input>(%s)+)$' % 
				(patt_userhost, patt_pth, patt_input)) + 
			('|^(?P<delayedinput>[$]{2} (%s)+)$' % (patt_input)) +
			'|^(?P<note>\(.*?\))$'
			'|^(?P<snippedoutput>[$]{2}-{3}(?: .+?)?)$'
			'|^(?P<output>.*?)$'
			, re.M | re.S)
	patt_input_tags = '(?P<ur>%s)|(?P<sq>%s)|(?P<dq>%s)|(?P<op>%s)|(?P<ct>%s)|(?P<wrd>%s)' % (patt_userreplacement, patt_singlequote, patt_doublequote, patt_cmdoption, patt_continuation, patt_wrd)
	regexp_tags = re.compile(patt_input_tags, re.S)
	regexp_ur = re.compile("(%s)" % (patt_userreplacement))

	def expand_macro(self, req, name, text, args):
		# args will be null if the macro is called without parenthesis.
		return self.render_macro(req, name, text);
		

	def render_macro(self, req, name, content):
		#if req.hdf:
		#	if not req.hdf.has_key("macro.ShellExample.outputcss"):
		#		req.hdf["macro.ShellExample.outputcss"] = True
		content = content and self.regex_crlf.sub("\n", escape(content).replace('&#34;', '"')) or ''
		def stringcallback(match):
			if match.group('ur'):
				return '<span class="code-input-userreplacement">' + match.group('ur') + '</span>'
			if match.group('sq'):
				m = self.regexp_ur.sub(r'<span class="code-input-userreplacement">\1</span>', match.group('sq'))
				return '<span class="code-input-string">' + m + '</span>'
			if match.group('dq'):
				m = self.regexp_ur.sub(r'<span class="code-input-userreplacement">\1</span>', match.group('dq'))
				return '<span class="code-input-string">' + m + '</span>'
			if match.group('ct'):
				return '<span class="code-input-continuation">' + match.group('ct') + '</span>'
			if match.group('op'):
				return '<span class="code-input-option">' + match.group('op') + '</span>'
			return match.group(0)

		def callback(match):
			m = match.group('cli')
			if m:
				path = match.group('path')
				if path:
					line = '<span class="code-path">' + path + '</span>'
				else:
					line = ''

				input = self.regexp_tags.sub(stringcallback, match.group('input'))
				input = '<span class="code-input">' + input + '</span>'
				if m == '# ':
					line = line + '<span class="code-root">' + m + input + '</span>'
				else:
					line = line + '<span class="code-user">' + m + input + '</span>'
				return line
			m = match.group('note')
			if m:
				return '<span class="code-note">' + m + '</span>'
			m = match.group('delayedinput')
			if m:
				inputdelayed = self.regexp_tags.sub(stringcallback, m[3:])
				return '<span class="code-input"><span class="code-delayed">' + inputdelayed + '</span></span>'
			m = match.group('snippedoutput')
			if m:
				sniptext = "&lt;Output Snipped&gt;" if len(m) == 5 else m[6:]
				return '<span class="code-output"><span class="code-snipped">' + sniptext + '</span></span>'
			m = match.group('output')
			if m:
				return '<span class="code-output">' + m + '</span>'
			return match.group(0)
		return Markup('<div class="code"><pre>' + self.regexp.sub(callback, content) + '</pre></div>');

	def get_templates_dirs(self):
		"""Return a list of directories containing the provided ClearSilver
		templates.
		"""
		return None

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
		self.log.info("Loading htdocs dir");
		from pkg_resources import resource_filename
		return [('shellexampleHdocs', resource_filename(__name__, 'htdocs'))]

	def match_request(self, req):
		"""
			Never Match a request but always load the css, trac seems
			to do some caching, so this only happens once per session?
		"""
		add_stylesheet(req, 'shellexampleHdocs/css/shellexample.css')
		return False;

	def process_request(self, req):
		"""
			This should never get called, as the match_request always 
			returns False
		"""
		return None, None
