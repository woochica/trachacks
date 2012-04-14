from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
#from trac.wiki.api import IWikiMacroProvider
from trac.web.main import IRequestHandler
from trac.util import escape
from genshi.core import Markup
from trac.wiki.macros import WikiMacroBase
import re

__all__ = ['ShellExample']

#######   Patterns   #######
PATT_PRINTABLE =       '[*-_./!@~a-zA-Z0-9]'
PATT_USERREPLACEMENT = '\{%s+\}' % (PATT_PRINTABLE)
PATT_SINGLEQUOTE =     "'.*?(?<!\\\\)'"
PATT_DOUBLEQUOTE =     '".*?(?<!\\\\)"'
PATT_CMDOPTION =       '(?<=\s)-{1,2}%s+=?' % (PATT_PRINTABLE)
PATT_CONTINUATION =    '\\\\\\n'
PATT_WRD =             '.*?'
PATT_PTH =             '(?P<path>[-~_ /a-zA-Z0-9]+)'
PATT_USERHOST =        '((?P<user>[-._a-zA-Z0-9]+)?(?P<userhostsep>@)?(?P<host>[-._a-zA-Z0-9]+)?)'
PATT_PS1START =        '(?P<ps1start>[\[({])'
PATT_PS1END =          '(?P<ps1end>[\])}:])'
PATT_CLI =             '(?P<cli>[#$](?![$])\s*)'
PATT_NOTE =            '^(?P<note>\(.*?\))$'
PATT_SNIPPEDOUTPUT =   '^(?P<snippedoutput>[$]{2}-{3}(?: .+?)?)$'
PATT_OUTPUT =          '^(?P<output>.*?)$'
PATT_INPUT =           '\s*%s|\s*%s|\s*%s|\s*%s|%s' % (PATT_USERREPLACEMENT, 
		                      PATT_SINGLEQUOTE, PATT_DOUBLEQUOTE, PATT_CONTINUATION, PATT_WRD)
PATT_DELAYEDINPUT =    '^(?P<delayedinput>[$]{2} (%s)+)$' % (PATT_INPUT)
PATT_PS1 =            ('(?P<preinput>(?P<ps1>%(ps1start)s?(%(userhost)s?(?P<userpathspace>\s*)%(path)s?)' +
		                 '%(ps1end)s?(?P<ps1endclispace>\s*))?%(cli)s)') % {
		                     'ps1start': PATT_PS1START, 'userhost': PATT_USERHOST, 'path': PATT_PTH, 
		                     'ps1end': PATT_PS1END, 'cli': PATT_CLI}
PATT_PRIMARYINPUT =   ('^(?P<primaryinput>%(ps1)s(?P<input>(%(input)s)+))$' % 
		                     {'ps1': PATT_PS1, 'input': PATT_INPUT})
PATT_INPUT_TAGS =     ('(?P<ur>%s)|(?P<sq>%s)|(?P<dq>%s)|(?P<op>%s)|(?P<ct>%s)|(?P<wrd>%s)' % 
		                     (PATT_USERREPLACEMENT, PATT_SINGLEQUOTE, PATT_DOUBLEQUOTE, 
									 PATT_CMDOPTION, PATT_CONTINUATION, PATT_WRD))

#######   Regular Expressions   #######
REGEX_CRLF = re.compile('''(\r\n|\r|\n)''')
REGEXP_LINE_MATCHER = re.compile(PATT_NOTE + '|' + 
		PATT_PRIMARYINPUT + '|' + PATT_DELAYEDINPUT + '|' + 
		PATT_SNIPPEDOUTPUT + '|' + PATT_OUTPUT, re.M | re.S)
REGEXP_TAGS = re.compile(PATT_INPUT_TAGS, re.S)
REGEXP_UR = re.compile("(%s)" % (PATT_USERREPLACEMENT))

class ShellExample(WikiMacroBase):
	implements(IRequestHandler, ITemplateProvider)
	revision = "$Rev$"
	url = "$URL$"


	def expand_macro(self, req, name, text, args):
		# args will be null if the macro is called without parenthesis.
		return self.render_macro(req, name, text);
		

	def render_macro(self, req, name, content):
		content = content and REGEX_CRLF.sub("\n", escape(content).replace('&#34;', '"')) or ''

		def inputstringcallback(match):
			if match.group('ur'):
				return '<span class="se-input-userreplacement">' + match.group('ur') + '</span>'
			if match.group('sq'):
				m = REGEXP_UR.sub(r'<span class="se-input-userreplacement">\1</span>', match.group('sq'))
				return '<span class="se-input-string">' + m + '</span>'
			if match.group('dq'):
				m = REGEXP_UR.sub(r'<span class="se-input-userreplacement">\1</span>', match.group('dq'))
				return '<span class="se-input-string">' + m + '</span>'
			if match.group('ct'):
				return '<span class="se-input-continuation">' + match.group('ct') + '</span>'
			if match.group('op'):
				return '<span class="se-input-option">' + match.group('op') + '</span>'
			return match.group(0)

		def linematcher_callback(match):
			if match.group('preinput'):
				s = ''
				if match.group('ps1'):
					if match.group('ps1start'):
						s += '<span class="se-prompt-start">' + match.group('ps1start') + '</span>'
					if match.group('user'):
						s += '<span class="se-prompt-user">' + match.group('user') + '</span>'
					if match.group('userhostsep'):
						s += '<span class="se-prompt-userhostseparator">' + match.group('userhostsep') + '</span>'
					if match.group('host'):
						s += '<span class="se-prompt-host">' + match.group('host') + '</span>'
					if match.group('userpathspace'):
						s += match.group('userpathspace')
					if match.group('path'):
						s += '<span class="se-prompt-path">' + match.group('path') + '</span>'
					if match.group('ps1end'):
						s += '<span class="se-prompt-end">' + match.group('ps1end') + '</span>'
					s = '<span class="se-prompt">' + s + '</span>';
				if match.group('cli'):
					if match.group('cli') == '# ':
						s += '<span class="se-root">' + match.group('cli') + '</span>'
					else:
						s += '<span class="se-unprivileged">' + match.group('cli') + '</span>'
					input = REGEXP_TAGS.sub(inputstringcallback, match.group('input'))
					s += '<span class="se-input">' + input + '</span>'
				return s;
			if match.group('note'):
				return '<span class="se-note">' + match.group('note') + '</span>'
			if match.group('delayedinput'):
				inputdelayed = REGEXP_TAGS.sub(inputstringcallback, match.group('delayedinput')[3:])
				return '<span class="se-input"><span class="se-input-delayed">' + inputdelayed + '</span></span>'
			if match.group('snippedoutput'):
				m = match.group('snippedoutput')
				# some one reported that this one-liner was causing a problem, but gave no details.
				# it does seem to work for me, however I have expanded it just in case. Ternary syntax
				# wasn't approved in python until 2.5 see Ticket #8858
				# sniptext = "&lt;Output Snipped&gt;" if len(m) == 5 else m[6:]
				if len(m) == 5:
					sniptext = "&lt;Output Snipped&gt;" 
				else:
					sniptext = m[6:]
				return '<span class="se-output"><span class="se-output-snipped">' + sniptext + '</span></span>'
			if match.group('output'):
				return '<span class="se-output">' + match.group('output') + '</span>'
			return match.group(0)

		return Markup('<div class="code"><pre>' + REGEXP_LINE_MATCHER.sub(linematcher_callback, content) + '</pre></div>');

	def get_templates_dirs(self):
		"""Return a list of directories containing the provided ClearSilver
		templates.
		"""
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
