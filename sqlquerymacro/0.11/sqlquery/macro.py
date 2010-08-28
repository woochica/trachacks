import inspect
from StringIO import StringIO

from trac.core import *
from trac.config import Option
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from trac.web.chrome import ITemplateProvider

from pymills.db import Connection
from pymills.datatypes import OrderedDict
from pymills.table import Table, Header, Row, Cell

__all__ = ["SqlQueryMacro"]

class SqlQueryMacro(Component):
	"""
	A macro to execute an SQL query against a
	configured database and render the results
	in a table.

	Example:
	{{{
	[[SQL(SELECT foo FROM bar)]]
	}}}
	"""
	
	implements(IWikiMacroProvider, ITemplateProvider)

	uri = Option("sqlquery", "uri", "sqlite://:memory:",
		"""Database URI to connect to and use for SQL Queries""")
	
	# IWikiMacroProvider methods
	def get_macros(self):
		yield "SQL"
		
	def get_macro_description(self, name):
		return inspect.getdoc(self.__class__)

	def expand_macro(self, formatter, name, args):
		if args is None:
			return "No query defined!"

		sql = str(args).strip()

		db = Connection(self.uri)
		try:
			records = db.do(sql)
		finally:
			db.rollback()
			db.close()

		if records:
			headers = []
			fields = [x for x in records[0].keys() if not x.startswith("__") and not x.endswith("__")]
			for field in fields:
				headers.append(Header(field))

			groups = OrderedDict()
			for record in records:
				style = ""

				if record.has_key("__color__"):
					style += "background-color: %s" % record["__color__"]
					record.remove("__color__")
				
				if record.has_key("__group__"):
					group = record["__group__"]
					record.remove("__group__")					
					row = Row([Cell(v) for v in record.values()],
						style=style)
					if not groups.has_key(group):
						groups[group] = []
					groups[group].append(row)
				else:
					row = Row([Cell(v) for v in record.values()],
						style=style)
					if not groups.has_key(None):
						groups[None] = []
					groups[None].append(row)

			s = StringIO()
			for group, rows in groups.iteritems():
				t = Table(headers, rows, cls="wiki")
				t.refresh()
				if group:
					s.write("=== %s ===\n" % group)
				s.write("{{{\n")
				s.write("#!html\n")
				s.write(t.toHTML())
				s.write("\n}}}\n")

			v = s.getvalue()
			s.close()
			return wiki_to_html(v, self.env, formatter.req)
		else:
			return "No results"

	# ITemplateProvider methods
	def get_templates_dirs(self):
		return []
		
	def get_htdocs_dirs(self):
		return []
	