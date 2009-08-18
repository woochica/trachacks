import inspect
import urllib
from StringIO import StringIO

from trac.core import *
from trac.config import Option
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from trac.web.chrome import ITemplateProvider

__all__ = ["SequenceDiagramMacro"]

class SequenceDiagramMacro(Component):
	"""
	A macro to include a Sequence Diagram from
	websequencediagrams.com
	"""
	
	implements(IWikiMacroProvider, ITemplateProvider)
	
	style = Option("sequencediagram", "style", "rose", "Diagram style")
	
	# IWikiMacroProvider methods
	def get_macros(self):
		yield "SequenceDiagram"
		
	def get_macro_description(self, name):
		return inspect.getdoc(self.__class__)

	def expand_macro(self, formatter, name, args):
		if args is None:
			return "No diagram text defined!"

		diagramText = str(args).strip()
		
		# First, encode the data.
		data = urllib.urlencode({"message" : diagramText, "style" : self.style, "paginate" : 0, "paper" : "letter", "landscape" : 0, "page" : 1, "format" : "png"})
		# Now get that file-like object again, remembering to mention the data.
		f = urllib.urlopen("http://www.websequencediagrams.com/index.php", data)
		# Read the results back.
		s = f.read()
		f.close()
		
		s = s[1:-1]
		seqargs = s.split(",")
		locargs = seqargs[0].split(":")
		loc = locargs[1].strip()
		loc = loc[1:-1]
		
		s = StringIO()
		s.write("{{{\n")
		s.write("#!html\n")
		s.write("<img src='http://www.websequencediagrams.com/%s'>" % loc)
		s.write("\n}}}\n")
		v = s.getvalue()
		s.close()
		
		return wiki_to_html(v, self.env, formatter.req)

	# ITemplateProvider methods
	def get_templates_dirs(self):
		return []
		
	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [("sqlquery", resource_filename(__name__, "htdocs"))]