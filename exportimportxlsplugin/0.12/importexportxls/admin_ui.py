# -*- coding: utf-8 -*-

# The MIT License
# 
# Copyright (c) 2011 ben.12
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time
import xlwt

from io import BytesIO


from trac import ticket
from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.util import Markup
from trac.util.datefmt import to_datetime
from trac.ticket.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider, Chrome
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query
from trac.mimeview.api import Mimeview, Context
from trac.resource import Resource

from importexportxls.formats import *

class ImportExportAdminPanel(Component):
    
    implements(ITemplateProvider, IAdminPanelProvider)

    _type = 'importexport'
    _label = ('Import/Export XLS', 'Import/Export XLS')

    def __init__(self):
        self.formats = {}
        self.formats['number'] = NumberFormat()
        self.formats['date'] = DateFormat()
        self.formats['text'] = TextFormat()
        self.formats['boolean'] = BooleanFormat()

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'importexport', 'Import/Export XLS') 

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TICKET_ADMIN')
        
        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()
        
        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]
        
        # get configurations:
        fieldsFormat = self._get_fields_format(allfields)
        fieldsExport = self._get_fields_export(allfields)
        fieldsImport = self._get_fields_import(allfields)
        
        if req.method == 'POST':
            # change custom fields excel types
            if req.args.get('save'):
                # clear actual config
                for name, value in self.config.options('import-export-xls'):
                    self.config.remove('import-export-xls', name)
                for cf in customfields:
                    fmt = req.args.get(cf['name']+'.format', 'text')
                    self.config.set('import-export-xls', cf['name']+'.format', fmt)
                    fieldsFormat[cf['name']] = fmt
                for cf in allfields:
                    fexport = bool( req.args.get(cf['name']+'.export', False) )
                    fimport = bool( req.args.get(cf['name']+'.import', False) )
                    if not fexport:
                        self.config.set('import-export-xls', cf['name']+'.export', fexport )
                    if not fimport:
                        self.config.set('import-export-xls', cf['name']+'.import', fimport )
                    fieldsExport[cf['name']] = fexport
                    fieldsImport[cf['name']] = fimport
                self.config.save()
            # change custom fields excel types
            if req.args.get('export'):
                self._send_export(req)
        
        
        settings = {}
        settings['defaultfields'] = defaultfields
        settings['customfields'] = customfields
        settings['formats'] = self.formats
        settings['fieldsFormat'] = fieldsFormat
        settings['fieldsExport'] = fieldsExport
        settings['fieldsImport'] = fieldsImport
        return 'importexport_webadminui.html', settings

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def _get_fields_format(self, fields = None):
        fieldsFormat = {}
        
        fieldnames = [f['name'] for f in fields]
        
        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()
        
        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]
        
        defaultfieldnames = [c['name'] for c in defaultfields]
        
        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]
        
        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsFormat[cf['name']] = self.config.get('import-export-xls', cf['name']+'.format', 'text')
        
        for fd in defaultfields:
            if fd['name'] in fieldnames:
                ftype = 'text'
                if fd['name'] in ['id']:
                    ftype = 'number'
                elif fd['name'] in ['time', 'changetime']:
                    ftype = 'date'
                fieldsFormat[fd['name']] = ftype
        
        return fieldsFormat


    def _get_fields_export(self, fields = None):
        fieldsExport = {}
        
        fieldnames = [f['name'] for f in fields]
        
        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()
        
        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]
        
        defaultfieldnames = [c['name'] for c in defaultfields]
        
        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]
        
        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsExport[cf['name']] = self.config.getbool('import-export-xls', cf['name']+'.export', True)
        
        for fd in defaultfields:
            if fd['name'] in fieldnames:
                fieldsExport[fd['name']] = self.config.getbool('import-export-xls', fd['name']+'.export', True)
        
        return fieldsExport

    def _get_fields_import(self, fields = None):
        fieldsImport = {}
        
        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()
        
        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]
        
        defaultfieldnames = [c['name'] for c in defaultfields]
        
        fields = fields or allfields
        fieldnames = [f['name'] for f in fields]
        
        for cf in customfields:
            if cf['name'] in fieldnames:
                fieldsImport[cf['name']] = self.config.getbool('import-export-xls', cf['name']+'.import', True)
        
        for fd in defaultfields:
            if fd['name'] in fieldnames:
                fieldsImport[fd['name']] = self.config.getbool('import-export-xls', fd['name']+'.import', True)
        
        return fieldsImport

    def _send_export(self, req):
        from trac.web import RequestDone 
        content, output_type = self._process_export(req)
        
        req.send_response(200) 
        req.send_header('Content-Type', output_type) 
        req.send_header('Content-Length', len(content)) 
        req.send_header('Content-Disposition', 'filename=tickets.xls') 
        req.end_headers() 
        req.write(content) 
        raise RequestDone

    def _process_export(self, req):
        fields = [ {'name':'id', 'label':'id'} ]
        fields.extend( TicketSystem(self.env).get_ticket_fields() )
        fieldsFormat = self._get_fields_format(fields)
        fieldsExport = self._get_fields_export(fields)
        
        fields = [c for c in fields if fieldsExport[ c['name'] ] ]
        fieldnames = [c['name'] for c in fields]
        
        query = Query(self.env, cols=fieldnames, order='id')
        
        content = BytesIO()
        cols = query.get_columns()
        
        headerStyle = xlwt.easyxf('font: bold on; pattern: pattern solid, fore-colour grey25; borders: top thin, bottom thin, left thin, right thin')
        
        wb = xlwt.Workbook()
        ws = wb.add_sheet('Tickets - %s' % self.config.get('project','name', '') )
        
        colIndex = {}
        c = 0
        for f in fields:
            ws.write(0, c, unicode(f['label']),headerStyle)
            colIndex[f['name']] = c
            c += 1
        
        context = Context.from_request(req)
        results = query.execute(req)
        r = 0
        for result in results:
            c = 0
            r += 1
            for col in cols:
                value = result[col]
                format = self.formats[ fieldsFormat[col] ]
                value = format.convert(value)
                style = format.get_style(value)
                ws.write(r, colIndex[col], value, style)
                c += 1
        wb.save(content)
        return (content.getvalue(), 'application/excel')
        
