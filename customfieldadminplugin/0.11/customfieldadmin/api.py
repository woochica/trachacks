# -*- coding: utf-8 -*-
"""
API for administrating custom ticket fields in Trac.
Supports creating, getting, updating and deleting custom fields.

License: BSD

(c) 2005-2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

from trac.core import *
from trac.ticket.model import TicketSystem
import re

__all__ = ['CustomFields']

class CustomFields(Component):
    """ These methods should be part of TicketSystem API/Data Model.
    Adds update_custom_field and delete_custom_field methods.
    (The get_custom_fields is already part of the API - just redirect here,
     and add option to only get one named field back.)
    """
    
    def get_custom_fields(self, env, customfield={}):
        """ Returns the custom fields from TicketSystem component.
        Use a cfdict with 'name' key set to find a specific custom field only
        """
        if not customfield:    # return full list
            return TicketSystem(env.compmgr).get_custom_fields()
        else:                  # only return specific item with cfname
            all = TicketSystem(env.compmgr).get_custom_fields()
            for item in all:
                if item['name'] == customfield['name']:
                    return item
            return None        # item not found
        
    def update_custom_field(self, env, customfield, create=False):
        """ Update or create a new custom field (if requested).
        customfield is a dictionary with the following possible keys:
            name = name of field (alphanumeric only)
            type = text|checkbox|select|radio|textarea
            label = label description
            value = default value for field content
            options = options for select and radio types (list, leave first empty for optional)
            cols = number of columns for text area
            rows = number of rows for text area
            order = specify sort order for field
        """
        # Name, Type and Label is required
        if not (customfield.has_key('name') and customfield.has_key('type') \
                and customfield.has_key('label')):
            raise TracError("Custom field needs at least a name, type and label.")
        # Use lowercase custom fieldnames only
        customfield['name'] = str(customfield['name']).lower()
        # Only alphanumeric characters (and [-_]) allowed for custom fieldname
        # Note: This is not pretty, but it works... Anyone have an eaier way of checking ???
        matchlen = re.search("[a-z0-9-_]+", customfield['name']).span()
        namelen = len(customfield['name'])
        if (matchlen[1]-matchlen[0] != namelen):
            raise TracError("Only alphanumeric characters allowed for custom field name (a-z or 0-9 or -_).")
        # If Create, check that field does not already exist
        if create and env.config.get('ticket-custom', customfield['name']):
            raise TracError("Can not create as field already exists.")
        # Check that it is a valid field type
        if not customfield['type'] in ['text', 'checkbox', 'select', 'radio', 'textarea']:
            raise TracError("%s is not a valid field type" % customfield['type'])
        # Create/update the field name and type
        env.config.set('ticket-custom', customfield['name'], customfield['type'])
        # Set the field label
        env.config.set('ticket-custom', customfield['name'] + '.label', customfield['label'])
        # Set default value if it exist in dictionay with value, else remove it if it exists in config
        if customfield.has_key('value') and customfield['value']:
            env.config.set('ticket-custom', customfield['name'] + '.value', customfield['value'])
        elif env.config.get('ticket-custom', customfield['name'] + '.value'):
            env.config.remove('ticket-custom', customfield['name'] + '.value')
        # If select or radio set options, or remove if it exists and field no longer need options
        if customfield['type'] in ['select', 'radio']:
            if not customfield.has_key('options') or customfield['options'] == []:
                raise TracError("No options specified for %s field" % customfield['type'])
            env.config.set('ticket-custom', customfield['name'] + '.options', '|'.join(customfield['options']))
        elif env.config.get('ticket-custom', customfield['name'] + '.options'):
            env.config.remove('ticket-custom', customfield['name'] + '.options')
        # Set defaults for textarea if none is specified, remove settings if no longer used
        if customfield['type'] == 'textarea':
            if (not customfield.has_key('cols')) or (not str(customfield['cols']).isdigit()):
                customfield['cols'] = "60"
            if (not customfield.has_key('rows')) or (not str(customfield['rows']).isdigit()):
                customfield['rows'] = "5"
            env.config.set('ticket-custom', customfield['name'] + '.cols', customfield['cols'])
            env.config.set('ticket-custom', customfield['name'] + '.rows', customfield['rows'])
        elif env.config.get('ticket-custom', customfield['name'] + '.cols'):
            env.config.remove('ticket-custom', customfield['name'] + '.cols')
        # Set sort setting if it is in customfield dict, remove if no longer present
        if create:
            last = len(self.get_custom_fields(env))
            env.config.set('ticket-custom', customfield['name'] + '.order',
                    customfield.get('order',0) or last)
        elif customfield.has_key('order') and customfield['order']:
            # Exists and have value - note: will not update order conflicting with other fields
            if str(customfield['order']).isdigit():
                env.config.set('ticket-custom', customfield['name'] + '.order', customfield['order'])
        elif env.config.get('ticket-custom', customfield['name'] + '.order'):
            env.config.remove('ticket-custom', customfield['name'] + '.order')
        # Save settings
        env.config.save()

    def delete_custom_field(self, env, customfield):
        """ Deletes a custom field.
        Input is a dictionary (see update_custom_field), but only ['name'] is required.
        """
        if not env.config.get('ticket-custom', customfield['name']):
            return # Nothing to do here - cannot find field
        # Need to redo the order of fields that are after the field to be deleted
        order_to_delete = env.config.getint('ticket-custom', customfield['name']+'.order')
        cfs = self.get_custom_fields(env)
        for field in cfs:
            if field['order'] > order_to_delete:
                env.config.set('ticket-custom', field['name']+'.order', field['order'] -1 )
        # Remove any data for the custom field (covering all bases)
        env.config.remove('ticket-custom', customfield['name'])
        env.config.remove('ticket-custom', customfield['name'] + '.label')
        env.config.remove('ticket-custom', customfield['name'] + '.value')
        env.config.remove('ticket-custom', customfield['name'] + '.options')
        env.config.remove('ticket-custom', customfield['name'] + '.cols')
        env.config.remove('ticket-custom', customfield['name'] + '.rows')
        env.config.remove('ticket-custom', customfield['name'] + '.order')
        # Save settings
        env.config.save()
