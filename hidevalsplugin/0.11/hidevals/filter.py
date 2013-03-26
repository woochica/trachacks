# Created by Noah Kantrowitz on 2007-04-02.
# Modified by Iker Jimenez on 2008-12-18. Based on a patch submited to
# http://trac-hacks.org/ticket/1920 by user kkas. 
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
# Copyright (c) 2008 Iker Jimenez. All rights reserved.

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

	def post_process_request(self, req, template, data, content_type):
		if (req.perm.has_permission('TRAC_ADMIN') 
		    or not req.perm.has_permission('TICKET_HIDEVALS')
		    or (not req.path_info.startswith('/newticket') 
			    and not req.path_info.startswith('/ticket') 
			    and not req.path_info.startswith('/query'))):
			# TRAC_ADMIN would have the filterer permissions by inheritance
			return (template, data, content_type)
		else:
			visible_fields = HideValsSystem(self.env).visible_fields(req)
			self.env.log.debug("visible_fields: %s" % str(visible_fields))			
			dont_filter = set(HideValsSystem(self.env).dont_filter)
			self.env.log.debug("dont_filter: %s" % str(dont_filter))			
			to_delete = []
			fields = data['fields']
			
			if req.path_info.startswith('/newticket') or req.path_info.startswith('/ticket'):
				for field in fields:
					if field['options'] and field['name'] not in dont_filter:
						if visible_fields.has_key(field['name']):
							# If we have any values, filter what is there
							# ???: Can a field have no options at this point? <NPK>
							opts = field['options']
							valid_opts = visible_fields[field['name']]
							opts_to_delete = []
							for opt in opts:
								if opt not in valid_opts:
									opts_to_delete.append(opt)
	
							for opt in opts_to_delete:
								self.env.log.debug("HideValsFilter: '%s' option removed from '%s' field" % (opt, field['name']))
								opts.remove(opt)
						else:
							# If there are no values for this user, remove the field entirely
							# NOTE: Deleting in place screws up the iteration, so do it all afterwards. <NPK>
							to_delete.append(field)
				for field in to_delete:
					self.env.log.debug("HideValsFilter: '%s' field removed" % field['name'])
					fields.remove(field)
			elif req.path_info.startswith('/query'):
				for field_name, field_value in fields.iteritems():
					if field_value.has_key('options') and field_value['options'] and field_name not in dont_filter:
						if visible_fields.has_key(field_name):
							# If we have any values, filter what is there
							# ???: Can a field have no options at this point? <NPK>
							opts = field_value['options']
							valid_opts = visible_fields[field_name]
							opts_to_delete = []
							for opt in opts:
								if opt not in valid_opts:
									opts_to_delete.append(opt)
	
							for opt in opts_to_delete:
								self.env.log.debug("HideValsFilter: '%s' option removed from '%s' field" % (opt, field_name))
								opts.remove(opt)
						else:
							# If there are no values for this user, remove the field entirely
							# NOTE: Deleting in place screws up the iteration, so do it all afterwards. <NPK>
							to_delete.append(field_name)
				for field_name in to_delete:
					self.env.log.debug("HideValsFilter: '%s' field removed" % field_name)
					del fields[field_name]
			return (template, data, content_type)
