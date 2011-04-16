# -*- coding: utf-8 -*-

from os import environ
from trac.core import *

try:
    import json
except:
    import simplejson as json

class LocaleUtil:

    def get_locale(self, req):
        """Get client locale from the http request."""
        
        locale = None
        locale_array = None
        
        if req.environ.has_key('HTTP_ACCEPT_LANGUAGE'):
            locale_array = req.environ['HTTP_ACCEPT_LANGUAGE'].split(",")
        
        if (len(locale_array) > 0):
            locale = locale_array[0].strip()
        
        if (len(locale) > 2):
            locale = locale[0:2];
        
        return locale


class TicketTemplate:
    
    # The new line replacement string
    _LB = '\\n'
    
    def process_tickettemplate(self, env, req, type_id='type'):
        
        ticket_type = req.args.get(type_id)
        template_field = self.get_template_field(env, ticket_type)
        
        response_data = {
            "template"     : template_field['template'],
            "enablefields" : template_field['enablefields'],
        }
        
        if hasattr(json, 'dumps'):
            # use simplejson(After python2.6 default)
            response = json.dumps(response_data);
            response = unicode(response, 'utf-8')
        elif hasattr(json, 'write'):
            # use json-py
            response = json.write(response_data);
        else:
            raise TracError('JSON library import error.')
        
        
        req.send_response(200)
        req.send_header('Content-Type', 'content=application/json; charset=UTF-8')
        req.send_header('Content-Length', len(response.encode('utf-8')))
        req.end_headers()
        
        req.write(response.encode('utf-8'))
        
    def get_template_field(self, env, type_name):
        """Get the ticket template field by the ticket type name.
        """
        
        if type_name == None:
            return {'name': '', 'template': '', 'enablefields': ''}
        
        template_key = type_name.encode('utf-8') + '.template'
        template = env.config.get('ticketext', template_key)
        template = template.replace(self._LB, '\n');
        
        enablefields_key = type_name.encode('utf-8') + '.enablefields'
        enablefields = env.config.get('ticketext', enablefields_key)
        
        template_field = {
            'name'         : type_name,
            'template'     : template,
            'enablefields' : enablefields
        }
        
        return template_field
    
    def update_template_field(self, env, template_field):
        """Update the ticket template field by the ticket type name.
        """
        
        if template_field == None:
            return
        
        type_name = template_field['name']
        template = template_field['template']
        enablefields = template_field['enablefields']
        
        if type_name == None:
            return
        
        template_key = type_name.encode('utf-8') + '.template'
        template = template.replace('\r\n', '\n');
        template = template.replace('\n', self._LB);
        env.config.set('ticketext', template_key, template)
        
        enablefields_key = type_name.encode('utf-8') + '.enablefields'
        env.config.set('ticketext', enablefields_key, enablefields)
        
        env.config.save()
