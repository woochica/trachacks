#!/usr/bin/env python
# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters.transform import Transformer
from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.util.translation import domain_functions
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script

_, tag_, N_, add_domain = domain_functions('HideFieldChanges', ('_', 'tag_', 'N_', 'add_domain'))

# functionality that implemented:
#  - hide specified fields
#  - add hide field button
#  - undone hiding fields

class HideFieldChanges(Component):
    implements(IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # when show a ticket, add script for 'hide customfield' buttons
        if req.path_info.startswith('/ticket'):
            add_script(req, 'common/js/hidefieldchanges.js')
                
        return handler
        
    def post_process_request(self, req, template, data, content_type):
        # check preconditions
        if template != 'ticket.html'\
                or not data \
                or not 'changes' in data \
                or not 'fields' in data \
                :
            return template, data, content_type
        hide_names = req.session.get('hidefieldchanges', '').split()
        # when submit 'Show these fields', set hiding-list
        if 'submit' in req.args and req.args['submit'] == u'Hide these fields':
            hide_names = [name for name in req.args if req.args[name] == 'on'] # override it
            self.log.debug('NAMES: %s' % hide_names)
            req.session['hidefieldchanges'] = ' '.join(hide_names)
        # when submit 'hide field', add it to hiding-list
        if 'hide' in req.args and req.args['hide'].startswith('hide '):
            label = req.args['hide'][5:]
            self.log.debug(label)
            names = [field['name'] for field in data['fields'] if field['label'] == label]
            for name in names:
                hide_names.append(name)
            req.session['hidefieldchanges'] = ' '.join(hide_names)
        # hide fields in changes
        if not 'showall' in req.args:
            for change in data['changes']:
                fields = change['fields']
                for key in hide_names:
                    if key in fields: del fields[key]
        # done
        return template, data, content_type

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [] # ResourceManager().resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        return [('common', ResourceManager().resource_filename(__name__, 'htdocs'))]

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        # check preconditions
        if filename != 'ticket.html':
            return stream
        transformer = Transformer()
        # build 'Hide these fields' Area
        hide_names = req.session.get('hidefieldchanges', [])
        hide_fields = []
        for field in data['fields']:
            name = field['name']
            checkbox = name in hide_names \
                and tag.input(type='checkbox', checked=True, name=name) \
                or tag.input(type='checkbox', name=name)
            hide_fields.append(tag.label(checkbox, field['label']))
            hide_fields.append(tag.br)
        hide_fields.append(tag.input(name='submit', type='submit', value='Hide these fields'))
        transformer = transformer \
            .select('//div[@id="changelog"]') \
            .before(tag.form(tag.input(value='hide changes', id='hidechangesbutton', type='button', style_='float: right;')
                             , tag.div(hide_fields, style='display: none', id='hidefields')
                             , action='#', class_='inlinebuttons hidechanges')).end()
        # build 'show all changes' button
#        showallbutton = tag.input(value='show all', name='showall', class_='showallbutton', type='submit', style_='float: right;')
#        showallbutton = tag.form(showallbutton, action='#', method='get', class_='inlinebuttons hidechanges')
#        transformer = transformer.select('//div[@id="changelog"]').before(showallbutton).end()
        # build 'hide customfield' buttons
        hidebutton = tag.input(value='hide', name="hide", class_='hidebutton', style_='display: none', type='submit')
        hidebutton = tag.form(hidebutton, action='#', method='get', class_='inlinebuttons hidefieldchanges')
        transformer = transformer \
            .select('//div[@id="changelog"]/div[@class="change"]/ul[@class="changes"]/li') \
            .prepend(hidebutton).end()
        # return filtered stream
        return stream | transformer
            
