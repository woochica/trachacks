# Created by Noah Kantrowitz on 2008-09-27.
# Copyright (c) 2008 Noah Kantrowitz. All rights reserved.
import logging

from trac.core import *
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.util.datefmt import to_datetime
from genshi.core import END
from genshi.builder import tag


class TracDeveloperHandler(logging.Handler):
    """A custom logging handler to implement the TracDeveloper log console."""
    
    def __init__(self):
        logging.Handler.__init__(self)
        self.buf = []
    
    def emit(self, record):
        self.buf.append(record)


class DeveloperLogModule(Component):
    """A plugin to display the Trac log."""

    implements(IRequestHandler, ITemplateStreamFilter)
    
    def __init__(self):
        # Force us to the front so we can override the default.
        from trac.core import ComponentMeta
        ComponentMeta._registry[IRequestHandler].remove(DeveloperLogModule)
        ComponentMeta._registry[IRequestHandler].insert(0, DeveloperLogModule)
    
    # IRequestHandler methods
    def match_request(self, req):
        if not req.path_info.startswith('/chrome'):
            hdlr = TracDeveloperHandler()
            hdlr.setFormatter(self.log._trac_handler.formatter)
            req._tracdeveloper_hdlr = hdlr
            self.log.addHandler(hdlr)
        return False

    def process_request(self, req):
        pass

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if not hasattr(req, '_tracdeveloper_hdlr'):
            return stream
        
        if method != 'xhtml':
            req._tracdeveloper_hdlr.formatter = None
            del req._tracdeveloper_hdlr.buf[:]
            self.log.removeHandler(req._tracdeveloper_hdlr)
            del req._tracdeveloper_hdlr
            return stream
        
        add_script(req, 'developer/js/log.js')
        
        def fn(stream):
            for kind, data, pos in stream:
                if kind is END and data.localname == 'body':
                    first_time = req._tracdeveloper_hdlr.buf \
                                 and req._tracdeveloper_hdlr.buf[0].created
                    
                    elm = tag.div(tag.table(tag.thead(tag.tr(
                        tag.th('Time'),
                        tag.th('Module'),
                        tag.th('Level'),
                        tag.th('Message'),
                    )), class_='listing')([
                        tag.tr(
                            tag.td(int((r.created - first_time) * 1000)),
                            tag.td(r.module),
                            tag.td(r.levelname),
                            tag.td(r.getMessage()),
                            class_=(i%2 and 'even' or 'odd'),
                        )
                        for i, r in enumerate(req._tracdeveloper_hdlr.buf)
                    ]), id='tracdeveloper-log')
                    for evt in elm.generate():
                        yield evt
                    del elm
                    req._tracdeveloper_hdlr.formatter = None
                    del req._tracdeveloper_hdlr.buf[:]
                    self.log.removeHandler(req._tracdeveloper_hdlr)
                    del req._tracdeveloper_hdlr
                yield kind, data, pos
        return stream | fn


