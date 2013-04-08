import re
import dbhelper
from trac import util
from trac.web.api import ITemplateStreamFilter
from trac.web.api import IRequestFilter
from trac.core import *
from genshi.core import *
from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.web.chrome import add_script

# This can go away once they fix http://genshi.edgewall.org/ticket/136
# At that point we should use Transformer.filter THIS IS STILL SOLVING
# PROBLEMS WELL AFTER THAT TICKET HAS BEEN CLOSED - A new ticket #290
# [1000] has fixed the bug, but is not the trac default yet Without
# this (using the default filter) I was getting omitted closing tags
# for some tags (Based on whitespace afaict)

class FilterTransformation(object):
    """Apply a normal stream filter to the selection. The filter is called once
    for each contiguous block of marked events."""

    def __init__(self, filter):
        """Create the transform.

        :param filter: The stream filter to apply.
        """
        self.filter = filter

    def __call__(self, stream):
        """Apply the transform filter to the marked stream.

        :param stream: The marked event stream to filter
        """
        def flush(queue):
            if queue:
                for event in self.filter(queue):
                    yield event
                del queue[:]

        queue = []
        for mark, event in stream:
            if mark:
                queue.append(event)
            else:
                for e in flush(queue):
                    yield None,e
                yield None,event
        for event in flush(queue):
            yield None,event

#@staticmethod
def disable_field(field_stream):
    value = Stream(field_stream).select('@value').render()
    
    for kind,data,pos in tag.span(value, id="field-totalhours").generate():
        yield kind,data,pos

class TotalHoursFilter(Component):
    """Disable editing of the Total Hours field so that we don't need Javascript."""
    implements(ITemplateStreamFilter)

    def match_stream(self, req, method, filename, stream, data):
        #self.log.debug("matching: ticket.html")
        return filename == 'ticket.html'

    def filter_stream(self, req, method, filename, stream, data):
        return stream | Transformer(
            '//input[@id="field-totalhours" and @type="text" and @name="field_totalhours"]'
            ).apply(FilterTransformation(disable_field))

class ReportsFilter(Component):
    """This component Removed rows from the report that require the 
       management screen to supply values"""
    implements(IRequestFilter)
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'report_list.html':
            add_script(req, "billing/report_filter.js")
        return (template, data, content_type)
