# $Id$

from trac.core import *
from trac.web.chrome import ITemplateStreamFilter
from genshi.filters.transform import Transformer, StreamBuffer

class PreCodeBrowserPlugin(Component):
	implements(ITemplateStreamFilter)

	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		filter = Transformer('//table[@class = "code"]')
		return stream | filter.rename('pre') \
			.select('thead').remove().end() \
			.select('tbody/tr/th').remove().end() \
			.select('tbody/tr/td').append('\n').unwrap()

