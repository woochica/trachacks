#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import implements, Component
from trac.ticket.default_workflow import get_workflow_config
from trac.web.api import ITemplateStreamFilter, IRequestHandler
from trac.web.chrome import add_script
try:
    import json
except:
    from tracrpc.json_rpc import json


class TicketValidatorDecolator(Component):
    implements(ITemplateStreamFilter, IRequestHandler)

    def __init__(self):
        self.rules = self._get_validation_rules()
        self.workflow = get_workflow_config(self.config)

    def _get_validation_rules(self):
        ''' compatible with TracTicketValidatorPlugin '''
        rules = {'summary': {'status': 'new'}}  # default rule
        for k, v in self.config.options('ticketvalidator'):
            if k == 'validate_author':
                pass
            elif k == 'validates':
                for v in self.config.getlist('ticketvalidator', k):
                    if v not in rules:
                        rules[v] = {}
            elif k.find('.') > 0:
                k, t = k.split('.', 1)
                rule = rules[k] if k in rules else {}
                rule[t] = v
                rules[k] = rule
            else:
                pass  # error, skip it
        # register rule in key as field-name if the rule have 'field'
        for key in rules.keys():
            if 'field' in rules[key]:
                field = rules[key]['field']
                rules[field] = rules.pop(key)
        return rules

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/ticketvalidator.options'

    def process_request(self, req):
        ''' return validation rules in json '''
        content = json.dumps({'rules': self.rules, 'workflow': self.workflow}, indent=4)
        req.send_response(200)
        req.send_header('Content-Type', 'application/json')
        req.send_header('Content-Length', len(content))
        req.end_headers()
        req.write(content)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename in [
                        'ticket.html',  # /ticket/{\d} or /newticket
                        ]:
            add_script(req, "contextchrome/js/ticketvalidatordecolator.js")
        return stream
