# Created by Noah Kantrowitz on 2007-04-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *
from trac.web.api import IRequestFilter

try:
    set = set
except NameError:
    from sets import Set as set

from api import HideValsSystem

class HideValsFilter(Component):
    """A filter to hide certain ticket field values."""

    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
            
    def post_process_request(self, req, template, content_type):
        if req.perm.has_permission('TRAC_ADMIN'):
            # TRAC_ADMIN would have the filterer permissions by inheritance
            return template, content_type
            
        if req.perm.has_permission('TICKET_HIDEVALS'):
            fields = HideValsSystem(self.env).visible_fields(req)
            dont_filter = set(HideValsSystem(self.env).dont_filter)
            to_delete = []
            
            base = None
            if req.path_info.startswith('/newticket'):
                base = 'newticket'
            elif req.path_info.startswith('/ticket'):
                base = 'ticket'
                
            if base:
                sub_hdf = req.hdf.getObj(base+'.fields').child()
                while sub_hdf:
                    if sub_hdf.getObj('options') and sub_hdf.name() not in dont_filter:
                        if sub_hdf.name() in fields:
                            # If we have any values, filter what is there
                            ###req.hdf.removeTree('newticket.fields.%s.options'%sub_hdf.name())
                            ###req.hdf['newticket.fields.%s.options'%sub_hdf.name()] = fields[sub_hdf.name()]
                            # ???: Can a field have no options at this point? <NPK>
                            opts = sub_hdf.getObj('options').child() 
                            valid_opts = set(fields[sub_hdf.name()])
                            opts_to_delete = []
                            while opts:
                                if opts.value() not in valid_opts:
                                    opts_to_delete.append(opts.name())
                                opts = opts.next()
                            
                            for opt in opts_to_delete:
                                req.hdf.removeTree('%s.fields.%s.options.%s'%(base, sub_hdf.name(), opt))
                        else:
                            # If there are no values for this user, remove the field entirely
                            # NOTE: Deleting in place screws up the iteration, so do it all afterwards. <NPK>
                            to_delete.append(sub_hdf.name())
                        
                    sub_hdf = sub_hdf.next()
                    
                for field in to_delete:
                    req.hdf.removeTree(base+'.fields.'+field)
                        
        return template, content_type