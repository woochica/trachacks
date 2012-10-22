# -*- coding: utf-8 -*-
# Copyright (C) 2008 Abbywinters.com
# trac-dev@abbywinters.com
# Contributor: Zach Miller

import re
from datetime import datetime

from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.config import ListOption
from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.ticket import TicketSystem
from trac.ticket.model import Ticket
from trac.ticket.notification import TicketNotifyEmail
from trac.util.datefmt import utc
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script
from trac.web.main import IRequestHandler


class GridModifyModule(Component):
    implements(IPermissionRequestor, IRequestHandler,
               ITemplateProvider, ITemplateStreamFilter)

    fields = ListOption('gridmodify', 'fields', '',
        doc="List of fields that will be modifiable.")

    # IPermissionRequestor methods
    def get_permission_actions(self):
        yield 'TICKET_GRID_MODIFY'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('gridmod', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
    
    # IRequestHandler methods
    def match_request(self, req):
        "Handle requests to /trac/gridmod URLs"
        return re.match(r'/gridmod(?:/.*)?$', req.path_info)

    def process_request(self, req):
        """Process AJAX request from select controls on modified query
           and report pages."""

        self.log.debug("GridModifyModule: process_request: entered")
        
        try:
            if(req.perm.has_permission('TICKET_ADMIN') or req.perm.has_permission('TICKET_GRID_MODIFY')):            

                self.log.debug("GridModifyModule: process_request: permissions OK")
                self.log.debug("GridModifyModule: process_request: req.args: %s", req.args)

                id = int(req.args.get('ticket'))
                ticket = Ticket(self.env, id)
                action = 'leave'

                # Save the action controllers we need to call side-effects for before
                # we save the changes to the ticket.
                controllers = list(self._get_action_controllers(req, ticket, action))

                for field in TicketSystem(self.env).get_ticket_fields():
                    field_name = field['name']

                    self.log.debug("  looking at field: '%s'", field_name)
                    self.log.debug("        type: %s", field['type'])
                    self.log.debug("        label: %s", field['label'])
                    self.log.debug("        ticket value['%s']: ", ticket[field_name])

                    if not field_name in req.args:
                        continue;
                    self.log.debug("  field '%s' in REQUEST", field_name)

                    val = req.args.get(field_name)
                    self.log.debug("        request value['%s']: %s", field_name, val)

                    if field['type'] == 'select':
                        if ((val in field['options']) or (val == '')):
                            self.log.debug("GridModifyModule: process_request: SELECT TAG: setting '%s' to '%s'.", field_name, val)
                            ticket[field_name] = val
                    elif field['type'] == 'text':
                        self.log.debug("GridModifyModule: process_request: INPUT TEXT TAG: setting '%s' to '%s'.", field_name, val)
                        ticket[field_name] = val
                    elif field['type'] == 'checkbox':
                        if val == 'True' or val == '1':
                            val = '1';
                        else:
                            val = '0';
                        self.log.debug("GridModifyModule: process_request: INPUT CHECKBOX TAG: setting '%s' to '%s'.", field_name, val)
                        ticket[field_name] = val
                    elif field['type'] == 'radio':
                        self.log.debug("GridModifyModule: process_request: INPUT RADIO TAG: setting '%s' to '%s'.", field_name, val)
                        ticket[field_name] = val

                    # Note: We are ignoring TextArea for now, as there are several complications including:
                    #   * Rendering is handled differently in the report form
                    #   * TextAreas support Wiki formatting so would need to use the Wiki engine

                now = datetime.now(utc)
                ticket.save_changes(req.authname, None, now)

                try:
                    tn = TicketNotifyEmail(self.env)
                    tn.notify(ticket, newticket=False, modtime=now)
                except Exception, e:
                    self.log.info("Failure sending notification on change to "
                                  "ticket #%s: %s" % (ticket.id, e))

                # After saving the changes, apply the side-effects.
                for controller in controllers:
                    self.env.log.info('Side effect for %s' % 
                                       controller.__class__.__name__)
                    controller.apply_action_side_effects(req, ticket, action)
            else:
                raise Exception('Permission denied')
        except Exception:
            import traceback
            self.log.error("GridModifyModule: Failure editing grid.\n" + traceback.format_exc())
            req.send_error(traceback.format_exc(), content_type='text/plain')
        else:
            req.send('OK', 'text/plain')

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, formdata):
        """Modifies query page to add modifiable components"""

        self.log.debug("GridModifyModule: filter_stream entered")

        # We create an invisible storage div in the document for the default tag values.
        # JQuery then uses this information to update the relevant fields on the page.


        if (filename == 'query.html' or filename == 'report_view.html') and \
           (req.perm.has_permission('TICKET_ADMIN') or req.perm.has_permission('TICKET_GRID_MODIFY')):
            add_script(req, 'gridmod/gridmod.js')
            xpath = '//div[@id="content"]'
            div = tag.div(id="table_inits_holder", style="display:none;")
            div.append("\n")

            for field in TicketSystem(self.env).get_ticket_fields():

                #debug
                self.log.debug("filter_stream: field: " + str(field))

                # SELECT tags
                if field['type'] == 'select' and (field['name'] in self.fields or len(self.fields) == 0):
                    select = tag.select(name=field['name'], class_="gridmod_form")
                    self.log.debug("SELECT INPUT '%s' (%s)", field['name'], field['label'])
                    if (field.has_key('value')):
                        self.log.debug("          SELECT HAS DEFAULT VALUE '%s'", field['value'])
                    else:
                        self.log.debug("          SELECT HAS NO DEFAULT VALUE")
                    # HACK: For some reason custom fields that have a blank value
                    # as a valid option don't actually have that blank
                    # value among the options in field['options'] so
                    # we force a blank option in in the case where the
                    # _default_ value is blank.
                    select.append("\n")
                    if(field.has_key('value') and field['value'] == '' and not ('' in field['options'])):
                        select.append(tag.option())
                    for option in field['options']:
                        select.append(tag.option(option, value=option))
                        select.append("\n")
                    div.append(select)

                # INPUT TEXT tags
                elif field['type'] == 'text' and field['name'] in self.fields:
                    text = tag.input(type='text', name=field['name'], class_='gridmod_form')
                    if(field.has_key('value')):
                        self.log.debug("TEXT INPUT '%s' (%s) HAS DEFAULT VALUE '%s'", field['name'], field['label'], field['value'])
                        text.append(field['value'])
                    else:
                        text.append('')

                    div.append(text)

                # INPUT CHECKBOX tags
                elif field['type'] == 'checkbox' and field['name'] in self.fields:
                    checkbox = tag.input(type='checkbox', name=field['name'], class_='gridmod_form')
                    if(field.has_key('value')):
                        self.log.debug("CHECKBOX INPUT '%s' (%s) HAS DEFAULT VALUE '%s'", field['name'], field['label'], field['value'])
                        checkbox.append(field['value'])
                        if (field['value'] == 1 or field['value'] == True):
                            checkbox(checked="checked")
                    else:
                        checkbox.append('0');

                    div.append(checkbox)

                # INPUT RADIO tags
                elif field['type'] == 'radio' and field['name'] in self.fields:
                    # This is slightly complicated.
                    # We convert the radio values into a SELECT tag for screen real estate reasons.
                    # It gets handled as a SELECT at the server end of the AJAX call, which appears to work fine.
                    # Note: If none of the RADIO buttons is checked, we default here to checking the first one, for code safety.
                    # That should never happen.
                    default_decided = False;
                    radio_select = tag.select(name=field['name'], class_="gridmod_form")
                    if(field.has_key('value')):
                        self.log.debug("RADIO INPUT '%s' (%s) HAS DEFAULT VALUE '%s'", field['name'], field['label'], field['value'])
                        default_val = field['value']
                        default_decided = True;
                    for option in field['options']:
                        self.log.debug("   doing radio option '%s'", option);
                        select_option = tag.option(option, value=option)
                        if (option == default_val) or (not default_decided):
                            self.log.debug("   SELECTED '%s'", option);
                            select_option(selected="selected")
                            default_decided = True;
                        radio_select.append(select_option)
                        radio_select.append("\n")

                    div.append(radio_select)

                div.append("\n"); 

                # INPUT TEXTAREA tags
                # We are ignoring TextArea for now, as there are several complications including:
                #   * Rendering is handled differently to other fields in the report form
                #   * TextAreas support Wiki formatting so would need to use the Wiki engine

            stream |= Transformer(xpath).append(div)
        return stream
            
    def _get_action_controllers(self, req, ticket, action):
        """Generator yielding the controllers handling the given `action`"""
        for controller in TicketSystem(self.env).action_controllers:
            actions = [a for w, a in
                       controller.get_ticket_actions(req, ticket)]
            if action in actions:
                yield controller

