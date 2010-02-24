# -*- coding: utf-8 -*-
"""
CalendarPopUp:
show selectable calendar pop-up where needed
"""

from pkg_resources import resource_filename

from trac.core import *

from trac.config import ListOption
from trac.web.chrome import add_script,add_stylesheet
from trac.web.chrome import ITemplateProvider 
from trac.web.chrome import ITemplateStreamFilter

from genshi.builder import Element
from genshi.filters.transform import Transformer

class CalendarPopUp(Component):

    implements(ITemplateProvider, ITemplateStreamFilter)

    insert_into = ListOption('calendarpopup', 'files', 'ticket.html,milestone_edit.html,admin_milestones.html',
        doc='List of files that calendarpopup should handle.')

    watch_ids = ListOption('calendarpopup', 'ids', 'field-due_assign,field-due_close,duedate=MM/dd/yy',
        doc='List of input ID\'s that should show calendarpopup. If date format of input field differs from yyyy/MM/dd, define it like duedate=MM/dd/yy')

    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('calendarpopup', resource_filename(__name__, 'htdocs'))]
          
    def get_templates_dirs(self):
        return []

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

    ## ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
    
    	found = False
    	for pattern in self.insert_into:
    		if filename == pattern:
    			add_stylesheet(req, 'calendarpopup/css/CalendarPopUp.css')
    			add_script(req, 'calendarpopup/js/CalendarPopUp.js')
    			found = True

    	calendarPopUpArrayOfIDs = ""
    	calendarPopUpArrayOfIDsFormat = ""
    	for element in self.watch_ids:
    		if element.find('=') != -1:
    			(one, two) = element.split('=', 2)
    			if one and two:
    				if calendarPopUpArrayOfIDs == "":
    					calendarPopUpArrayOfIDs = "\"%s\"" % one
    					calendarPopUpArrayOfIDsFormat = "\"%s\"" % two
    				else:
    					calendarPopUpArrayOfIDs = "%s, \"%s\"" % (calendarPopUpArrayOfIDs, one)
    					calendarPopUpArrayOfIDsFormat = "%s, \"%s\"" % (calendarPopUpArrayOfIDsFormat, two)
    		else:
    			if element:
    				if calendarPopUpArrayOfIDs == "":
    					calendarPopUpArrayOfIDs = "\"%s\"" % element
    					calendarPopUpArrayOfIDsFormat = "\"yyyy/MM/dd\""
    				else:
    					calendarPopUpArrayOfIDs = "%s, \"%s\"" % (calendarPopUpArrayOfIDs, element)
    					calendarPopUpArrayOfIDsFormat = "%s, \"yyyy/MM/dd\"" % calendarPopUpArrayOfIDsFormat

        
    	insertDIV = Element('div', id="CalendarPopUpDiv", style="position:absolute;visibility:hidden;background-color:white;layer-background-color:white;")
    	insertScript = Element('script', type="text/javascript")('var calendarPopUpArrayOfIDs = new Array(%s); var calendarPopUpArrayOfIDsFormat = new Array(%s)' % (calendarPopUpArrayOfIDs, calendarPopUpArrayOfIDsFormat) )
    	
    	if found:
    		return stream | Transformer('//div[@id="footer"]').after(insertDIV) | Transformer('body').before(insertScript)
		
    	return stream
