
#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import encodings
import os
import re
import shutil
import tempfile
import time
import unicodedata

from trac.core import *
from trac.attachment import AttachmentModule
from trac.core import Component
from trac.config import Option
from trac.perm import IPermissionRequestor
from trac.ticket import TicketSystem
from trac.ticket import model
from trac.util import get_reporter_id
from trac.util.compat import set, sorted
from trac.util.html import html
from trac.util.text import to_unicode
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider

from talm_importer.processors import ImportProcessor
from talm_importer.processors import PreviewProcessor
from talm_importer.readers import get_reader


class ImportModule(Component):
    csv_default_encoding = Option('importer', 'csv_default_encoding', 'utf-8',
        doc="Default encoding of CSV file")

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'importer'

    def get_navigation_items(self, req):
        if not req.perm.has_permission('IMPORT_EXECUTE'):
            return
        yield ('mainnav', 'importer',
               html.a('Import', href=req.href.importer()))

    # IPermissionRequestor methods  
    def get_permission_actions(self):  
	return ['IMPORT_EXECUTE']  

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/importer(?:/([0-9]+))?', req.path_info)
        if match:
            return True

    def process_request(self, req):
        req.perm.assert_permission('IMPORT_EXECUTE')
        action = req.args.get('action', 'other')

        if req.args.has_key('cancel'):
            req.redirect(req.href('importer'))
                
        if action == 'upload' and req.method == 'POST':
            req.session['importer.uploadedfile'] = None
            uploadedfilename, uploadedfile = self._save_uploaded_file(req)
            req.session['importer.sheet'] = req.args['sheet']
            req.session['importer.encoding'] = req.args['encoding']
            req.session['importer.uploadedfile'] = uploadedfile
            req.session['importer.uploadedfilename'] = uploadedfilename
            req.session['importer.tickettime'] = str(int(time.time()))
            return self._do_preview(uploadedfile, int(req.session['importer.sheet']), req,
                                    encoding=req.session['importer.encoding'])
        elif action == 'import' and req.method == 'POST':
            tickettime = int(req.session['importer.tickettime'])
            if tickettime == 0:
                raise TracError('No time set since preview, unable to import: please upload the file again')

            return self._do_import(req.session['importer.uploadedfile'], int(req.session['importer.sheet']),
                                   req, req.session['importer.uploadedfilename'], tickettime,
                                   encoding=req.session['importer.encoding'])
            
        else:
            req.session['importer.uploadedfile'] = None
            req.session['importer.uploadedfilename'] = None

            data = { 'reconciliate_by_owner_also': self._reconciliate_by_owner_also(),
                     'fields': ['ticket or id'] + [field['name'] for field in TicketSystem(self.env).get_ticket_fields()],
                     'csv_default_encoding': self.csv_default_encoding,
                     'encodings': self._get_encodings() }

            return 'importer.html', data, None

    # ITemplateProvider

    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _datetime_format(self):
        return str(self.config.get('importer', 'datetime_format', '%x')) # default is Locale's appropriate date representation

    def _do_preview(self, uploadedfile, sheet, req, encoding=None):
        filereader = get_reader(uploadedfile, sheet, self._datetime_format(), encoding=encoding)
        try:
            return self._process(filereader, get_reporter_id(req), PreviewProcessor(self.env, req))
        finally:
            filereader.close()

    def _do_import(self, uploadedfile, sheet, req, uploadedfilename, tickettime, encoding=None):
        filereader = get_reader(uploadedfile, sheet, self._datetime_format(), encoding=encoding)
        try:
            try:
                return self._process(filereader, get_reporter_id(req), ImportProcessor(self.env, req, uploadedfilename, tickettime))
            finally:
                filereader.close()
        except:
            # Unlock the database. This is not really tested, but seems reasonable. TODO: test or verify this
            self.env.get_db_cnx().rollback()
            raise


    def _save_uploaded_file(self, req):
        req.perm.assert_permission('IMPORT_EXECUTE')
        
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
        
        # We try to normalize the filename to unicode NFC if we can.
        # Files uploaded from OS X might be in NFD.
        filename = unicodedata.normalize('NFC', unicode(upload.filename,
                                                        'utf-8'))
        filename = filename.replace('\\', '/').replace(':', '/')
        filename = os.path.basename(filename)
        if not filename:
            raise TracError('No file uploaded')

        return filename, self._savedata(upload.file)


    def _savedata(self, fileobj):

        # temp folder
        tempuploadedfile = tempfile.mktemp()

        flags = os.O_CREAT + os.O_WRONLY + os.O_EXCL
        if hasattr(os, 'O_BINARY'):
            flags += os.O_BINARY
        targetfile = os.fdopen(os.open(tempuploadedfile, flags), 'w')
 
        try:
            shutil.copyfileobj(fileobj, targetfile)
        finally:
            targetfile.close()
        return tempuploadedfile



    def _process(self, filereader, reporter, processor):
        tracfields = [field['name'] for field in TicketSystem(self.env).get_ticket_fields()]
        tracfields = [ 'ticket', 'id' ] + tracfields
        customfields = [field['name'] for field in TicketSystem(self.env).get_custom_fields()]

        columns, rows = filereader.readers()

        importedfields = [f for f in columns if f.lower() in tracfields]
        notimportedfields = [f for f in columns if f and (f.lower() not in tracfields + ['comment']
                                                          # relative fields will be added later
                                                          and f[0] != '#')]
        commentfields = [f for f in columns if f.lower() == 'comment']
        if commentfields:
            commentfield = commentfields[0]
        else:
            commentfield = None
        lowercaseimportedfields = [f.lower() for f in importedfields]

        # Fields which contain relative ticket numbers to update after import
        relativeticketfields = []
        lowercaserelativeticketfields = []
        for f in columns:
            if not f.startswith('#'):
                continue
            if f[1:].lower() in tracfields:
                relativeticketfields.append(f)
                lowercaserelativeticketfields.append(f[1:].lower())
            else:
                notimportedfields.append(f)

        idcolumn = None

        if 'ticket' in lowercaseimportedfields and 'id' in lowercaseimportedfields:
            raise TracError, 'The first line of the worksheet contains both \'ticket\', and an \'id\' field name. Only one of them is needed to perform the import. Please check the file and try again.'

        ownercolumn = None
        if 'ticket' in lowercaseimportedfields:
            idcolumn = self._find_case_insensitive('ticket', importedfields)
        elif 'id' in lowercaseimportedfields:
            idcolumn = self._find_case_insensitive('id', importedfields)
        elif 'summary' in lowercaseimportedfields:
            summarycolumn = self._find_case_insensitive('summary', importedfields)
            ownercolumn = self._reconciliate_by_owner_also() and self._find_case_insensitive('owner', importedfields) or None
        else:
            raise TracError, 'The first line of the worksheet contains neither a \'ticket\', an \'id\' nor a \'summary\' field name. At least one of them is needed to perform the import. Please check the file and try again.'

        # start TODO: this is too complex, it should be replaced by a call to TicketSystem(env).get_ticket_fields()
        
        # The fields that we will have to set a value for, if:
        #    - they are not in the imported fields, and 
        #    - they are not set in the default values of the Ticket class, and
        #    - they shouldn't be set to empty
        # if 'set' is true, this will be the value that will be set by default (even if the default value in the Ticket class is different)
        # if 'set' is false, the value is computed by Trac and we don't have anything to do
        computedfields = {'status':      { 'value':'new',         'set': True }, 
                          'resolution' : { 'value': "''(None)''", 'set': False }, 
                          'reporter' :   { 'value': reporter,     'set': True  }, 
                          'time' :       { 'value': "''(now)''",  'set': False }, 
                          'changetime' : { 'value': "''(now)''",  'set': False } }

        if 'owner' not in lowercaseimportedfields and 'component' in lowercaseimportedfields:
            computedfields['owner'] = {}
            computedfields['owner']['value'] = 'Computed from component'
            computedfields['owner']['set'] = False

        # to get the computed default values
        from ticket import PatchedTicket
        ticket = PatchedTicket(self.env)
        
        for f in [ 'type', 'cc' , 'description', 'keywords', 'component' , 'severity' , 'priority' , 'version', 'milestone' ] + customfields:
            if f in ticket.values:
                computedfields[f] = {}
                computedfields[f]['value'] = ticket.values[f]
                computedfields[f]['set'] = False
            else:
                computedfields[f] = None

        processor.start(importedfields, ownercolumn != None, commentfield)

        missingfields = [f for f in computedfields if f not in lowercaseimportedfields]

        if relativeticketfields:
            missingfields = [f for f in missingfields if f not in lowercaserelativeticketfields]
        missingemptyfields = [ f for f in missingfields if computedfields[f] == None or computedfields[f]['value'] == '']
        missingdefaultedfields = [ f for f in missingfields if f not in missingemptyfields]

        if  missingfields != []:
            processor.process_missing_fields(missingfields, missingemptyfields, missingdefaultedfields, computedfields)

        # end TODO: this is too complex
        if notimportedfields != []:
            processor.process_notimported_fields(notimportedfields)

        if commentfield:
            processor.process_comment_field(commentfield)

        # TODO: test the cases where those fields have empty values. They should be handled as None. (just to test, may be working already :)
        selects = [
            #Those ones inherit from AbstractEnum
            ('type', model.Type), 
            ('status', model.Status),
            ('priority', model.Priority),
            ('severity', model.Severity),
            ('resolution', model.Resolution),
            #Those don't
            ('milestone', model.Milestone),
            ('component', model.Component),
            ('version', model.Version)
            ]
        existingvalues = {}
        newvalues = {}
        for name, cls in selects:
            if name not in lowercaseimportedfields:
                # this field is not present, nothing to do 
                continue
            
            options = [val.name for val in cls.select(self.env)]
            if not options:
                # Fields without possible values are treated as if they didn't
                # exist
                continue
            existingvalues[name] = options
            newvalues[name] = []
            

        def add_sql_result(db, aset, queries):
            cursor = db.cursor()
            for query in queries:
                cursor.execute(query)
                aset.update([val for val, in cursor])

        existingusers = set()
        db = self.env.get_db_cnx()
        add_sql_result(
            db, existingusers,
            [("SELECT DISTINCT reporter FROM ticket"
              " WHERE reporter IS NOT NULL AND reporter != ''"),
             ("SELECT DISTINCT owner FROM ticket"
              " WHERE owner IS NOT NULL AND owner != ''"),
             ("SELECT DISTINCT owner FROM component"
              " WHERE owner IS NOT NULL AND owner != ''")])
        for username, name, email in self.env.get_known_users(db):
            existingusers.add(username)
        newusers = []

        duplicate_summaries = []

        relativeticketvalues = []
        row_idx = 0

        for row in rows:
            if idcolumn:
                ticket_id = row[idcolumn].strip()
                if ticket_id:
                    ticket_id = ticket_id.lstrip('#')
                if ticket_id:
                    self._check_ticket(db, ticket_id)
                else:
                    # will create a new ticket
                    ticket_id = 0
            else:
                summary = row[summarycolumn]
                owner = ownercolumn and row[ownercolumn] or None
                if self._skip_lines_with_empty_owner() and ownercolumn and not owner:
                    continue

                ticket_id = self._find_ticket(db, summary, owner)
                if (summary, owner) in duplicate_summaries:
                    if owner == None:
                        raise TracError, 'Summary "%s" is duplicated in the spreadsheet. Ticket reconciliation by summary can not be done. Please modify the summaries in the spreadsheet to ensure that they are unique.' % summary
                    else:
                        raise TracError, 'Summary "%s" and owner "%s" are duplicated in the spreadsheet. Ticket reconciliation can not be done. Please modify the summaries in the spreadsheet to ensure that they are unique.' % (summary, owner)
                        
                else:
                    duplicate_summaries += [ (summary, owner) ]
                    

            processor.start_process_row(row_idx, ticket_id)

            for column in importedfields:
                cell = row[column]
                if cell is None:
                    cell = ''
                column_lower = column.lower()
                
                # collect the new lookup values
                if column_lower in existingvalues:
                    if isinstance(cell, basestring):
                        cell = cell.strip()
                    if cell != '' and \
                            cell not in existingvalues[column_lower] and \
                            cell not in newvalues[column_lower]:
                        newvalues[column_lower].append(cell)

                # also collect the new user names
                if column_lower in ('owner', 'reporter'):
                    if cell != '' and \
                            cell not in newusers and \
                            cell not in existingusers:
                        newusers.append(cell)

                # and proces the value.
                if column_lower not in ('ticket', 'id'):
                    processor.process_cell(column, cell)
                
            if commentfield:
                processor.process_comment(row[commentfield])

            relativeticketvalues.append(dict([(f[1:].lower(), row[f]) 
                                              for f in relativeticketfields]))

            processor.end_process_row()
            row_idx += 1


        # All the rows have been processed.  Handle global stuff
        for name in list(newvalues):
            if not newvalues[name]:
                del newvalues[name]

        if newvalues:
            processor.process_new_lookups(newvalues)
            
        if newusers:
            processor.process_new_users(newusers)

        if relativeticketfields:
            processor.process_relativeticket_fields(relativeticketvalues, lowercaserelativeticketfields)

        return processor.end_process(row_idx)


    def _reconciliate_by_owner_also(self):
        return self.config.getbool('importer', 'reconciliate_by_owner_also', False)

    def _skip_lines_with_empty_owner(self):
        return self.config.getbool('importer', 'skip_lines_with_empty_owner', False)

    def _find_case_insensitive(self, value, list):
        '''
        Find case-insentively; returns the last (i.e. random !) element if not found
        
        >>> from trac.env import Environment
        >>> import os
        >>> instancedir = os.path.join(tempfile.gettempdir(), 'test-importer._find_case_insensitive')
        >>> for root, dirs, files in os.walk(instancedir, topdown=False):
        ...     for name in files:
        ...         os.remove(os.path.join(root, name))
        ...     for name in dirs:
        ...         os.rmdir(os.path.join(root, name))
        ...
        >>> env = Environment(instancedir, create=True)
        >>> importmodule = ImportModule(env)
        >>> importmodule._find_case_insensitive('aa', ['Aa', 'Bb', 'Cc'])
        'Aa'
        >>> importmodule._find_case_insensitive('aa', ['Cc', 'Aa', 'Bb'])
        'Aa'
        >>> importmodule._find_case_insensitive('aa', ['Cc', 'Bb', 'Aa'])
        'Aa'
        >>> importmodule._find_case_insensitive('dd', ['Aa', 'Cc', 'Bb'])
        '''
        found = reduce(lambda x, y: ((y.lower() == value.lower()) and y or x), list)
        return ((found.lower() == value.lower()) and found or None)

    def _find_ticket(self, db, summary, owner = None):
        '''
        Finds the ticket(s) with the given summary

        >>> from trac.env import Environment
        >>> import os
        >>> instancedir = os.path.join(tempfile.gettempdir(), 'test-importer._find_ticket')
        >>> for root, dirs, files in os.walk(instancedir, topdown=False):
        ...     for name in files:
        ...         os.remove(os.path.join(root, name))
        ...     for name in dirs:
        ...         os.rmdir(os.path.join(root, name))
        ...
        >>> env = Environment(instancedir, create=True)
        >>> db = env.get_db_cnx()
        >>> cursor = db.cursor()
        >>> importmodule = ImportModule(env)
        >>> def _exec(cursor, sql, args = None): cursor.execute(sql, args)
        >>> _exec(cursor, "insert into ticket (id, summary) values (%s, %s)", [1235, 'AAAA'])
        >>> _exec(cursor, "insert into ticket (id, summary) values (%s, %s)", [1236, "AA\'AA"])
        >>> _exec(cursor, "insert into ticket (id, summary) values (%s, %s)", [1237, "BBBB"])
        >>> _exec(cursor, "insert into ticket (id, summary) values (%s, %s)", [1238, "BBBB"])
        >>> db.commit()
        >>> importmodule._find_ticket(db, 'AAAA')
        1235
        >>> importmodule._find_ticket(db, "AA\'AA")
        1236
        >>> importmodule._find_ticket(db, 'AA')
        0
        >>> try: importmodule._find_ticket(db, 'BBBB') 
        ... except TracError, err_string: print err_string
        Tickets #1237 and #1238 have the same summary "BBBB" in Trac. Ticket reconciliation by summary can not be done. Please modify the summaries to ensure that they are unique.
        >>> _exec(cursor, "delete from ticket where ID in (1235, 1236, 1237, 1238)")
        >>> db.commit()
        >>> #_exec(cursor, "select ticket,time,author,field,oldvalue,newvalue from ticket_change where time > 1190603709")        
        >>> _exec(cursor, "delete from ticket where id = 489")
        >>> db.commit()
        >>> #print cursor.fetchall()
        >>> #importmodule._find_ticket(db, u'clusterization')
        '''
        cursor = db.cursor()
        if owner == None:
            cursor.execute('SELECT id FROM ticket WHERE summary = %s', [ summary ] )
        else:
            cursor.execute('SELECT id FROM ticket WHERE summary = %s and owner = %s', [ summary, owner ] )
        rows = cursor.fetchall()
        if len(rows) > 1:
            raise TracError('Tickets %s and %s have the same summary "%s" in Trac. Ticket reconciliation by summary can not be done. Please modify the summaries to ensure that they are unique.' % (reduce(lambda x, y: x + ', ' + y, ['#' + str(row[0]) for row in rows[0:-1]]), '#' + str(rows[-1][0]), summary))
        elif len(rows) == 1:
            return int(rows[0][0])
        else:
            return 0

    def _check_ticket(self, db, ticket_id):
        ticket_id = to_unicode(ticket_id)
        cursor = db.cursor()
        cursor.execute('SELECT summary FROM ticket WHERE id = %s', (ticket_id,))
        row = cursor.fetchone()
        if not row:
            raise TracError('Ticket %s found in file, but not present in Trac: cannot import.' % ticket_id)
        return row[0]

    def _get_encodings(self):
        encs = set(encodings.aliases.aliases.values())
        for enc in ('base64_codec', 'bz2_codec', 'hex_codec', 'quopri_codec',
                    'rot_13', 'uu_codec', 'zlib_codec'):
            encs.discard(enc)
        return sorted(list(enc.replace('_', '-') for enc in encs))
        
if __name__ == '__main__': 
    import doctest
    testfolder = __file__
    doctest.testmod()
