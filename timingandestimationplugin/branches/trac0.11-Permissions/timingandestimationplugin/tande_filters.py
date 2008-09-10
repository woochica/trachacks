from trac.web.api import ITemplateStreamFilter
from trac.perm import IPermissionRequestor
from trac.core import *
from genshi.core import *
from genshi.builder import tag
from sets import Set as set
from genshi.filters.transform import Transformer
from blackmagic import *

class TimePermissionFilter(Component):
    """Filtering the streams based on permissions to edit touch various fields"""
    implements(ITemplateStreamFilter, IPermissionRequestor)
    # IPermissionRequestor methods 
    def get_permission_actions(self): 
        return ["TIME_VIEW", "TIME_RECORD", ("TIME_ADMIN", ["TIME_RECORD", "TIME_VIEW"])] 


    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug("TimePermissionFilter executing") 
        if not filename == 'ticket.html':
            self.log.debug("TimePermissionFilter not the correct template")
            return stream
        
        self.log.debug("TimePermissionFilter Always disabling totalhours")
        stream = disable_field(stream, "totalhours")
        stream = remove_header(stream, "hours")

#         if not req.perm.has_permission("TIME_VIEW"):
#             self.log.debug("TimePermissionFilter: No TIME_VIEW! removing billable and total hours")
#             stream = remove_field(stream, "billable")
#             stream = remove_field(stream, "totalhours")
#         if not req.perm.has_permission("TIME_RECORD"):
#             self.log.debug("TimePermissionFilter matching: No TIME_RECORD removing hours making billable and estimatedhours disabled")
#             stream = remove_field(stream, "hours")
#             stream = disable_field(stream, "billable")
#             stream = disable_field(stream, "estimatedhours")

        return stream 
