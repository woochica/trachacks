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
        sentinel = 'sentinel'  # something that isn't None
        conditionkeys = ['status', 'type']
        conditionkeys.sort()
        rules = {'status=new&type=*': {'summary': sentinel}}
        ''' compatible with TracTicketValidatorPlugin '''
        keys = [k[:-4] for k, v in self.config.options('ticketvalidator') if k.endswith('.rule')]  # includes dot
        for key in keys:
            values = dict([(k[len(key):], v) for k, v in self.config.options('ticketvalidator') if k.startswith(key)])
            condition = '&'.join(['%s=%s' % (ck, values.get(ck, '*')) for ck in conditionkeys])
            if condition not in rules:
                rules[condition] = {}
            rule = rules.get(condition)
            field = values.get('field', key[:-1])
            rule[field] = values.get('tip', sentinel)
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
