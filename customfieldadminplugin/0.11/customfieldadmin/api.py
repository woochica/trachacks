# -*- coding: utf-8 -*-
"""
API for administrating custom ticket fields in Trac.
Supports creating, getting, updating and deleting custom fields.

License: BSD

(c) 2005-2012 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import re

from pkg_resources import resource_filename

from trac.core import *
from trac.ticket.api import TicketSystem

try:
    from  trac.util.translation import domain_functions
    add_domain, _, tag_ = \
        domain_functions('customfieldadmin', ('add_domain', '_', 'tag_'))
except:
    # fall back to 0.11 behavior, i18n functions are no-ops then
    from genshi.builder import tag as tag_
    from trac.util.translation import gettext as _
    def add_domain(*args, **kwargs):
        pass

__all__ = ['CustomFields']

class CustomFields(Component):
    """ These methods should be part of TicketSystem API/Data Model.
    Adds update_custom_field and delete_custom_field methods.
    (The get_custom_fields is already part of the API - just redirect here,
     and add option to only get one named field back.)
    
    Input to methods is a 'customfield' dict supporting these keys:
        name = name of field (alphanumeric only)
        type = text|checkbox|select|radio|textarea
        label = label description
        value = default value for field content
        options = options for select and radio types (list, leave first empty for optional)
        cols = number of columns for text area
        rows = number of rows for text area
        order = specify sort order for field
        format = text|wiki (for text and textarea)
    """
    
    implements()
    
    config_options = ['label', 'value', 'options', 'cols', 'rows',
                         'order', 'format']
    
    def __init__(self):
        # bind the 'customfieldadmin' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)
        
    def get_custom_fields(self, customfield=None):
        """ Returns the custom fields from TicketSystem component.
        Use a cfdict with 'name' key set to find a specific custom field only.
        """
        if not customfield:    # return full list
            return TicketSystem(self.env).get_custom_fields()
        else:                  # only return specific item with cfname
            all = TicketSystem(self.env).get_custom_fields()
            for item in all:
                if item['name'] == customfield['name']:
                    return item
            return None        # item not found
    
    def verify_custom_field(self, customfield, create=True):
        """ Basic validation of the input for modifying or creating
        custom fields. """
        # Name, Type and Label is required
        if not (customfield.get('name') and customfield.get('type') \
                and customfield.get('label')):
            raise TracError(
                    _("Custom field needs at least a name, type and label."))
        # Use lowercase custom fieldnames only
        customfield['name'] = customfield['name'].lower()
        # Only alphanumeric characters (and [-_]) allowed for custom fieldname
        if re.search('^[a-z][a-z0-9_]+$', customfield['name']) == None:
           raise TracError(_("Only alphanumeric characters allowed for " \
                             "custom field name ('a-z' or '0-9' or '_'), " \
                             "with 'a-z' as first character."))
        # Name must begin with a character - anything else not supported by Trac
        if not customfield['name'][0].isalpha():
            raise TracError(
                    _("Custom field name must begin with a character (a-z)."))
        # Check that it is a valid field type
        if not customfield['type'] in ['text', 'checkbox', 'select', 'radio', 'textarea']:
            raise TracError(_("%(field_type)s is not a valid field type"),
                                        field_type=customfield['type'])
        # Check that field does not already exist (if modify it should already be deleted)
        if create and self.config.get('ticket-custom', customfield['name']):
            raise TracError(_("Can not create as field already exists."))
    
    def create_custom_field(self, customfield):
        """ Create the new custom fields (that may just have been deleted as part
        of 'modify'). Note: Caller is responsible for verifying input before create."""
        # Set the mandatory items
        self.config.set('ticket-custom', customfield['name'], customfield['type'])
        self.config.set('ticket-custom', customfield['name'] + '.label', customfield['label'])
        # Optional items
        if 'value' in customfield:
            self.config.set('ticket-custom', customfield['name'] + '.value', customfield['value'])
        if 'options' in customfield:
            if customfield.get('optional', False):
                self.config.set('ticket-custom', customfield['name'] + '.options',
                                '|' + '|'.join(customfield['options']))
            else:
                self.config.set('ticket-custom', customfield['name'] + '.options',
                               '|'.join(customfield['options'])) 
        if 'format' in customfield and customfield['type'] in ('text', 'textarea'):
            self.config.set('ticket-custom', customfield['name'] + '.format', customfield['format'])
        # Textarea
        if customfield['type'] == 'textarea':
            cols = customfield.get('cols') and int(customfield.get('cols', 0)) > 0 \
                                                and customfield.get('cols') or 60
            rows = customfield.get('rows', 0) and int(customfield.get('rows', 0)) > 0 \
                                                and customfield.get('rows') or 5
            self.config.set('ticket-custom', customfield['name'] + '.cols', cols)
            self.config.set('ticket-custom', customfield['name'] + '.rows', rows)
        # Order
        order = customfield.get('order', "")
        if order == "":
            order = len(self.get_custom_fields())
        self.config.set('ticket-custom', customfield['name'] + '.order', order)
        self.config.save()

    def update_custom_field(self, customfield, create=False):
        """ Updates a custom. Option to 'create' is kept in order to keep
        the API backwards compatible. """
        if create:
            self.verify_custom_field(customfield)
            self.create_custom_field(customfield)
            return
        # Check input, then delete and save new
        self.verify_custom_field(customfield, create=False)
        self.delete_custom_field(customfield, modify=True)
        self.create_custom_field(customfield)
    
    def delete_custom_field(self, customfield, modify=False):
        """ Deletes a custom field.
        Input is a dictionary (see update_custom_field), but only ['name'] is required.
        """
        if not self.config.get('ticket-custom', customfield['name']):
            return # Nothing to do here - cannot find field
        if not modify:
            # Permanent delete - reorder later fields to lower order
            order_to_delete = self.config.getint('ticket-custom', customfield['name']+'.order')
            cfs = self.get_custom_fields()
            for field in cfs:
                if field['order'] > order_to_delete:
                    self.config.set('ticket-custom', field['name']+'.order', field['order'] -1 )
        supported_options = [customfield['name']] + \
            [customfield['name']+'.'+opt for opt in self.config_options]
        for option, _value in self.config.options('ticket-custom'):
            if modify and not option in supported_options:
                # Only delete supported options when modifying
                # http://trac-hacks.org/ticket/8188
                continue
            if option == customfield['name'] \
                    or option.startswith(customfield['name'] + '.'):
                self.config.remove('ticket-custom', option)
        # Persist permanent deletes
        if not modify:
            self.config.save()
