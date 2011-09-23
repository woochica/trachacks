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

import sys
import os
import tempfile
import shutil
import time
import xlwt
import xlrd

# ticket #8805 : unavailable for python 2.4 or 2.5
# from io import BytesIO
import cStringIO


from trac import ticket
from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.util import Markup
from trac.util.datefmt import to_datetime
from trac.ticket.admin import IAdminPanelProvider
from trac.web.chrome import add_script, ITemplateProvider, Chrome
from trac.ticket.api import TicketSystem
from trac.ticket.query import Query
from trac.ticket.model import Ticket
from trac.mimeview.api import Mimeview, Context
from trac.resource import Resource
from trac.attachment import AttachmentModule

from importexportxls.formats import *

class ImportExportAdminPanel(Component):
    
    implements(ITemplateProvider, IPermissionRequestor, IAdminPanelProvider)

    _type = 'importexport'
    _label = ('Import/Export XLS', 'Import/Export XLS')

    def __init__(self):
        self.formats = {}
        self.formats['number'] = NumberFormat(self.config)
        self.formats['datetime'] = DateTimeFormat(self.config)
        self.formats['date'] = DateFormat(self.config)
        self.formats['text'] = TextFormat(self.config)
        self.formats['boolean'] = BooleanFormat(self.config)
        
        self.exportForced = ['id', 'summary']
        self.importForbidden = ['id', 'summary', 'time', 'changetime']

    # IPermissionRequestor methods  
    def get_permission_actions(self):  
        return ['TICKET_ADMIN']  

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', 'Ticket System', 'importexport', 'Import/Export XLS') 

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('TICKET_ADMIN')
        
        template = 'importexport_webadminui.html'
        
        allfields = [ {'name':'id', 'label':'id'} ]
        allfields.extend( TicketSystem(self.env).get_ticket_fields() )
        customfields = TicketSystem(self.env).get_custom_fields()
        
        customfieldnames = [c['name'] for c in customfields]
        defaultfields = [c for c in allfields if c['name'] not in customfieldnames]
        
        # get configurations:
        fieldsFormat = self._get_fields_format(allfields)
        fieldsExport = self._get_fields_export(allfields)
        fieldsImport = self._get_fields_import(allfields)
        
        settings = {}
        
        if req.method == 'POST':
            # change custom fields excel types
            if req.args.get('save'):
                # clear actual config
                for name, value in self.config.options('import-export-xls'):
                    self.config.remove('import-export-xls', name)
                # change custom fields excel types
                for cf in customfields:
                    fmt = req.args.get(cf['name']+'.format', 'text')
                    self.config.set('import-export-xls', cf['name']+'.format', fmt)
                    fieldsFormat[cf['name']] = fmt
                # change fields exported and imported
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
            if req.args.get('export'):
                self._send_export(req)
            if req.args.get('import_preview'):
                (settings['tickets'], settings['importedFields'], settings['warnings']) = self._get_import_preview(req)
                template = 'importexport_preview.html'
                add_script(req, "importexportxls/importexport_preview.js")
            if req.args.get('import'):
                settings = self._process_import(req)
                template = 'importexport_done.html'
        
        
        settings['endofline'] = self.config.get('import-export-xls', 'endofline', 'LF')
        settings['defaultfields'] = defaultfields
        settings['customfields'] = customfields
        settings['formats'] = self.formats
        settings['fieldsFormat'] = fieldsFormat
        settings['fieldsExport'] = fieldsExport
        settings['fieldsImport'] = fieldsImport
        settings['exportForced'] = self.exportForced
        settings['importForbidden'] = self.importForbidden
        settings['req'] = req
        return template, settings

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('importexportxls', resource_filename(__name__, 'htdocs'))]

    def _get_fields_format(self, fields = None):
        fieldsFormat = {}
        
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
                    ftype = 'datetime'
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
        
        for fd in self.exportForced:
            fieldsExport[fd] = True
        
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
        
        
        for fd in self.importForbidden:
            fieldsImport[fd] = False
        
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
        
        # ticket #8805 : unavailable for python 2.4 or 2.5
        #content = BytesIO()
        content = cStringIO.StringIO()
        
        headerStyle = xlwt.easyxf('font: bold on; pattern: pattern solid, fore-colour grey25; borders: top thin, bottom thin, left thin, right thin')
        
        wb = xlwt.Workbook()
        try:
          ws = wb.add_sheet('Tickets - %s' % self.config.get('project','name', '') )
        except:
          # Project name incompatible with sheet name constraints.
          ws = wb.add_sheet('Tickets')
        
        colIndex = {}
        c = 0
        for f in fields:
            ws.write(0, c, unicode(f['label']),headerStyle)
            colIndex[f['name']] = c
            c += 1
        
        query = Query(self.env, cols=fieldnames, order='id', max=sys.maxint)
        results = query.execute(req)
        r = 0
        cols = query.get_columns()
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
    
    
    def _get_import_preview(self, req):
        req.perm.assert_permission('TICKET_ADMIN')
        
        tempfile = self._save_uploaded_file(req)
        
        if req.session.has_key('importexportxls.tempfile') and os.path.isfile(req.session['importexportxls.tempfile']):
          try:
            # some times tempfile leave opened
            os.remove( req.session['importexportxls.tempfile'] )
          except:
            exc = sys.exc_info()
        req.session['importexportxls.tempfile'] = tempfile
        
        return self._get_tickets(tempfile)

    def _process_import(self, req):
        req.perm.assert_permission('TICKET_ADMIN')
        
        added = 0
        modified = 0;        
        
        if req.session.has_key('importexportxls.tempfile'):
          tempfile = req.session['importexportxls.tempfile']
          del req.session['importexportxls.tempfile']
          
          tickets, importFields, warnings = self._get_tickets(tempfile)
          try:
            # some times tempfile leave opened
            os.remove( tempfile )
          except:
            exc = sys.exc_info()
          
          for i, t in enumerate(tickets):
            if bool( req.args.get('ticket.'+unicode(i), False) ):
              if t.exists:
                if t.save_changes(author=util.get_reporter_id(req)):
                  modified += 1
              else:
                t.insert()
                added += 1
        return {'added':added,'modified':modified}
    
    def _get_tickets(self, filename):
        fieldsLabels = TicketSystem(self.env).get_ticket_field_labels()
        fieldsLabels['id'] = 'id'
        
        invFieldsLabels = {}
        for k in fieldsLabels.keys():
            invFieldsLabels[fieldsLabels[k]] = k
        
        book = xlrd.open_workbook(filename)
        sh = book.sheet_by_index(0)
        columns = [unicode(sh.cell_value(0, c)) for c in range(sh.ncols)]
        
        # columns "id" and "summary" are needed
        if 'id' not in columns and fieldsLabels['id'] not in columns:
            raise TracError('Column "id" not found')
        if 'summary' not in columns and fieldsLabels['summary'] not in columns:
            raise TracError('Column "summary" not found')
        
        fieldsImport = self._get_fields_import()
        
        importFields = []
        columnsIds = {}
        idx = 0
        idIndex = 0
        summaryIndex = 0
        creationIndex = None
        modificationIndex = None
        for c in columns:
            if c not in fieldsLabels.keys() and c in fieldsLabels.values():
                columnsIds[idx] = invFieldsLabels[c]
                if fieldsImport[invFieldsLabels[c]]:
                    importFields.append({'name':invFieldsLabels[c], 'label':c})
            elif c in fieldsLabels.keys() and c not in fieldsLabels.values():
                columnsIds[idx] = c
                if fieldsImport[c]:
                    importFields.append({'name':c, 'label':fieldsLabels[c]})
            else:
                columnsIds[idx] = None
            if columnsIds[idx] == 'id':
                idIndex = idx
            if columnsIds[idx] == 'summary':
                summaryIndex = idx
            if columnsIds[idx] == 'time':
                creationIndex = idx
            if columnsIds[idx] == 'changetime':
                modificationIndex = idx
            idx += 1
                      
        fieldsFormat = self._get_fields_format( importFields + [{'name':'id', 'label':'id'}, {'name':'summary', 'label':fieldsLabels['summary']}] )
        
        warnings = []
        preview = []
        for r in range(1, sh.nrows):
            tid = self.formats['number'].restore( sh.cell_value(r, idIndex) )
            summary = self.formats['text'].restore( sh.cell_value(r, summaryIndex) )
            if tid == '' or tid == None:
                ticket = Ticket(self.env)
                for k in fieldsLabels.keys():
                    ticket[k] = ticket.get_value_or_default(k)
                ticket['summary'] = summary
            else:
                ticket = Ticket(self.env, tkt_id=tid)
                if ticket['summary'] != summary:
                    warnings.append('You cannot modify the summary for the ticket #'+unicode(tid))
            
            for idx in columnsIds.keys():
                col = columnsIds[idx]
                if col != None and idx not in [idIndex, summaryIndex, creationIndex, modificationIndex] and col in fieldsFormat.keys():
                    converterId = fieldsFormat[col]
                    converter = self.formats[converterId];
                    value = sh.cell_value(r, idx)
                    value = converter.restore( value )
                    if converter.convert( value ) != converter.convert( ticket[col] ) and converter.convert( value ) != unicode('--'):
                        ticket[col] = value
            preview.append(ticket)
            
        return (preview, importFields, warnings)
    
    def _save_uploaded_file(self, req):
        req.perm.assert_permission('TICKET_ADMIN')
        
        upload = req.args['import-file']
        if not hasattr(upload, 'filename') or not upload.filename:
            raise TracError('No file uploaded')
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2) # seek to end of file
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError("Can't upload empty file")
        
        # Maximum file size (in bytes)
        max_size = AttachmentModule.max_size
        if max_size >= 0 and size > max_size:
            raise TracError('Maximum file size (same as attachment size, set in trac.ini configuration file): %d bytes' % max_size,
                            'Upload failed')
        
        # temp folder
        tempuploadedfile = tempfile.mktemp()

        flags = os.O_CREAT + os.O_WRONLY + os.O_EXCL
        if hasattr(os, 'O_BINARY'):
            flags += os.O_BINARY
        targetfile = os.fdopen(os.open(tempuploadedfile, flags), 'w')
 
        try:
            shutil.copyfileobj(upload.file, targetfile)
        finally:
            targetfile.close()
        return tempuploadedfile
