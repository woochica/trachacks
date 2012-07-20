#
# Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
# Author: Francois Granade - fg at nexb dot com
# Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense
#

import time

from trac.ticket import Ticket, model
from trac.util import get_reporter_id
from trac.util.datefmt import format_datetime
from trac.util.html import Markup
from trac.util.text import to_unicode
from trac.wiki import wiki_to_html


class ImportProcessor(object):
    def __init__(self, env, req, filename, tickettime):
        self.env = env
        self.req = req
        self.filename = filename
        self.modified = {}
        self.added = {}

        # TODO: check that the tickets haven't changed since preview
        self.tickettime = tickettime
        
        # Keep the db to commit it all at once at the end
        self.db = self.env.get_db_cnx()
        self.missingemptyfields = None
        self.missingdefaultedfields = None
        self.computedfields = None
        self.importedfields = None

    def start(self, importedfields, reconciliate_by_owner_also, has_comments):
        # Index by row index, returns ticket id
        self.crossref = []
        self.lowercaseimportedfields = [f.lower() for f in importedfields]

    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.missingemptyfields = missingemptyfields
        self.missingdefaultedfields = missingdefaultedfields
        self.computedfields = computedfields

    def process_notimported_fields(self, notimportedfields):
        pass

    def process_comment_field(self, comment):
        pass

    def start_process_row(self, row_idx, ticket_id):
        from ticket import PatchedTicket
        if ticket_id > 0:
            # existing ticket
            self.ticket = PatchedTicket(self.env, tkt_id=ticket_id, db=self.db)

            # 'Ticket.time_changed' is a datetime in 0.11, and an int in 0.10.
            # if we have trac.util.datefmt.to_datetime, we're likely with 0.11
            try:
                from trac.util.datefmt import to_timestamp
                time_changed = to_timestamp(self.ticket.time_changed)
            except ImportError:
                time_changed = int(self.ticket.time_changed)
                
            if time_changed > self.tickettime:
                # just in case, verify if it wouldn't be a ticket that has been modified in the future
                # (of course, it shouldn't happen... but who know). If it's the case, don't report it as an error
                if time_changed < int(time.time()):
                    # TODO: this is not working yet...
                    #
                    #raise TracError("Sorry, can not execute the import. "
                    #"The ticket #" + str(ticket_id) + " has been modified by someone else "
                    #"since preview. You must re-upload and preview your file to avoid overwriting the other changes.")
                    pass

        else:
            self.ticket = PatchedTicket(self.env, db=self.db)
        self.comment = ''

    def process_cell(self, column, cell):
        cell = unicode(cell)
        column = column.lower()
        # if status of new ticket is empty, force to use 'new'
        if not self.ticket.exists and column == 'status' and not cell:
            cell = 'new'
        # this will ensure that the changes are logged, see model.py Ticket.__setitem__
        self.ticket[column] = cell

    def process_comment(self, comment):
        self.comment = comment

    def end_process_row(self):
        try:
            # 'when' is a datetime in 0.11, and an int in 0.10.
            # if we have trac.util.datefmt.to_datetime, we're likely with 0.11
            from trac.util.datefmt import to_datetime
            tickettime = to_datetime(self.tickettime)
        except ImportError:
            tickettime = self.tickettime
                
        if self.ticket.id == None:
            if self.missingemptyfields:
                for f in self.missingemptyfields:
                    if f in self.ticket.values and self.ticket[f] is None:
                        self.ticket[f] = ''

            if self.comment:
                self.ticket['description'] = self.ticket['description'] + "\n[[BR]][[BR]]\n''Batch insert from file " + self.filename + ":''\n" + self.comment

            if self.computedfields:
                for f in self.computedfields:
                    if f not in self.lowercaseimportedfields and \
                            self.computedfields[f] is not None and \
                            self.computedfields[f]['set']:
                        self.ticket[f] = self.computedfields[f]['value']

            self.ticket.insert(when=tickettime, db=self.db)
            self.added[self.ticket.id] = 1
        else:
            if self.comment:
                message = "''Batch update from file " + self.filename + ":'' " + self.comment
            else:
                message = "''Batch update from file " + self.filename + "''"
            if self.ticket.is_modified() or self.comment:
                self.ticket.save_changes(get_reporter_id(self.req), message, when=tickettime, db=self.db) # TODO: handle cnum, cnum = ticket.values['cnum'] + 1)
                self.modified[self.ticket.id] = 1

        self.crossref.append(self.ticket.id)
        self.ticket = None

    def process_new_lookups(self, newvalues):
        for field, names in newvalues.iteritems():
            if field == 'status':
                continue
            
            LOOKUPS = {  'component': model.Component,
                         'milestone': model.Milestone,
                         'version':  model.Version,
                         'type': model.Type,
                         }
            try:
                CurrentLookupEnum = LOOKUPS[field]
            except KeyError:
                class CurrentLookupEnum(model.AbstractEnum):
                    # here, you shouldn't put 'self.' before the class field.
                    type = field

            for name in names:
                lookup = CurrentLookupEnum(self.env, db=self.db)
                lookup.name = name
                lookup.insert()

    def process_new_users(self, newusers):
        pass

    # Rows is an array of dictionaries.
    # Each row is indexed by the field names in relativeticketfields.
    def process_relativeticket_fields(self, rows, relativeticketfields):
        from ticket import PatchedTicket
        
        # Find the WBS columns, if any.  We never expect to have more
        # than one but this is flexible and easy.  There's no good
        # reason to go to the trouble of ignoring extras.
        wbsfields=[]
        for row in rows:
            for f in relativeticketfields:
                if row[f].find('.') != -1:
                    if f not in wbsfields:
                        wbsfields.append(f)


        # If WBS column present, build reverse lookup to find the
        # ticket ID from a WBS number.
        wbsref = {}
        if wbsfields != []:
            row_idx = 0
            for row in rows:
                wbsref[row[wbsfields[0]]] = self.crossref[row_idx]
                row_idx += 1

        row_idx = 0
        for row in rows:
            id = self.crossref[row_idx]

            # Get the ticket (added or updated in the main loop
            ticket = PatchedTicket(self.env, tkt_id=id, db=self.db)

            for f in relativeticketfields:
                # Get the value of the relative field column (e.g., "2,3")
                v = row[f]
                # If it's not empty, process the contents
                if len(v) > 0:
                    # Handle WBS numbers
                    if f in wbsfields:
                        if row[f].find('.') == -1:
                            # Top level, no parent
                            ticket[f] = ''
                        else:
                            # Get this task's wbs
                            wbs = row[f]
                            # Remove the last dot-delimited field
                            pwbs = wbs[:wbs.rindex(".")]
                            # Look up the parent's ticket ID
                            ticket[f] = str(wbsref[pwbs])
                    # Handle dependencies
                    else:
                        s = []
                        for r in v.split(","):
                            # Make the string value an integer
                            r = int(r)

                            # The relative ticket dependencies are 1-based,
                            # array indices are 0-based.  Convert and look up
                            # the new ticket ID of the other ticket.
                            i = self.crossref[r-1]

                            # TODO check that i != id

                            s.append(str(i))

                        # Empty or not, use it to update the ticket
                        ticket[f] = ', '.join(s)


            ticket.save_changes(get_reporter_id(self.req), '', db=self.db)
            row_idx += 1
        
            
    def end_process(self, numrows):
        self.db.commit()

        data = {}
        data['title'] = 'Import completed'
        #data['report.title'] = data['title'].lower()
        notmodifiedcount = numrows - len(self.added) - len(self.modified)

        message = 'Successfully imported ' + str(numrows) + ' tickets (' + str(len(self.added)) + ' added, ' + str(len(self.modified)) + ' modified, ' + str(notmodifiedcount) + ' unchanged).'

        data['message'] = Markup("<style type=\"text/css\">#report-notfound { display:none; }</style>\n") + wiki_to_html(message, self.env, self.req)

        return 'import_preview.html', data, None
    

class PreviewProcessor(object):
    
    def __init__(self, env, req):
        self.env = env
        self.req = req
        self.data = {'rows': []}
        self.ticket = None
        self.rowmodified = False
        self.styles = ''
        self.duplicatessumaries = []
        self.modified = {}
        self.added = {}

    def start(self, importedfields, reconciliate_by_owner_also, has_comments):
        self.data['title'] = 'Preview Import'

        self.message = u''

        if 'ticket' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'ticket\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n' 
        elif 'id' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'id\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n' 
        else:
            self.message += ' * A \'\'\'ticket\'\'\' column was not found: tickets will be reconciliated by summary' + (reconciliate_by_owner_also and ' and by owner' or '') + '. If an existing ticket with the same summary' + (reconciliate_by_owner_also and ' and the same owner' or '') + ' is found, values that are changing appear in italics in the preview below. If no ticket with same summary ' + (reconciliate_by_owner_also and ' and same owner' or '') + 'is found, the whole line appears in italics below, and a new ticket will be added.\n' 
                                
        self.data['headers'] = [{ 'col': 'ticket', 'title': 'ticket' }]
        # we use one more color to set a style for all fields in a row... the CS templates happens 'color' + color + '-odd'
        self.styles = "<style type=\"text/css\">\n.ticket-imported, .modified-ticket-imported { width: 40px; }\n"
        self.styles += ".color-new-odd td, .color-new-even td, .modified-ticket-imported"
        columns = importedfields[:]
        if has_comments:
            columns.append('comment')

        for col in columns:
            if col.lower() != 'ticket' and col.lower() != 'id':
                title=col.capitalize()
                self.data['headers'].append({ 'col': col, 'title': title })
                self.styles += ", .modified-%s" % col
        self.styles += " { font-style: italic; }\n"
        self.styles += "</style>\n"

    # This could be simplified...
    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.message += ' * Some Trac fields are not present in the import. They will default to:\n\n'
        self.message += "   ||'''field'''||'''Default value'''||\n"
        if missingemptyfields != []:
            self.message += u"   ||%s||''(Empty value)''||\n" \
                            % u', '.join([to_unicode(x.capitalize()) for x in missingemptyfields])
            
        if missingdefaultedfields != []:
            for f in missingdefaultedfields:
                self.message += u'   ||%s||%s||\n' % (to_unicode(f.capitalize()), computedfields[f]['value'])

        self.message += '(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n'

    def process_notimported_fields(self, notimportedfields):
        self.message += u' * Some fields will not be imported because they don\'t exist in Trac: %s.\n' \
                        % u', '.join([x and to_unicode(x) or u"''(empty name)''" for x in notimportedfields])

    # Rows is an array of arrays.
    # Each row is indexed by the field names in relativeticketfields.
    def process_relativeticket_fields(self, rows, relativeticketfields):
        self.message += ' * Relative ticket numbers will be processed in: ' + ', '.join([x and x or "''(empty name)''" for x in relativeticketfields])  + '.\n'
        wbsfields=[]
        for row in rows:
            for f in relativeticketfields:
                self.env.log.debug("f %s, row '%s'" % (f, row[f]))
                if row[f].find('.') != -1:
                    self.env.log.debug("found")
                    if f not in wbsfields:
                        wbsfields.append(f)
        if wbsfields != []:
            self.message += '    WBS numbers processed in: ' + ', '.join([x and x or "''(empty name)''" for x in wbsfields])  + '.\n'
            
    def process_comment_field(self, comment):
        self.message += u' * The field "%s" will be used as comment when modifying tickets, and appended to the description for new tickets.\n' % comment

    def start_process_row(self, row_idx, ticket_id):
        from ticket import PatchedTicket
        self.ticket = None
        self.cells = []
        self.rowmodified = False
        self.row_idx = row_idx
        if ticket_id > 0:
            # existing ticket. Load the ticket, to see which fields will be modified
            self.ticket = PatchedTicket(self.env, ticket_id)
            

    def process_cell(self, column, cell):
        if self.ticket and not (self.ticket.values.has_key(column.lower()) and self.ticket[column.lower()] == cell):
            self.cells.append( { 'col': column, 'value': cell, 'style': 'modified-' + column })
            self.rowmodified = True
        else:
            # if status of new ticket is empty, force to use 'new'
            if not self.ticket and column.lower() == 'status' and not cell:
                cell = 'new'
            self.cells.append( { 'col': column, 'value': cell, 'style': column })

    def process_comment(self, comment):
        column = 'comment'
        self.cells.append( { 'col': column, 'value': comment, 'style': column })

    def end_process_row(self):
        odd = len(self.data['rows']) % 2
        if self.ticket:
            if self.rowmodified:
                self.modified[self.ticket.id] = 1
                style = ''
                ticket = self.ticket.id
            else:
                style = ''
                ticket = self.ticket.id
        else: 
            self.added[self.row_idx] = 1
            style = odd and 'color-new-odd' or 'color-new-even'
            ticket = '(new)'
            
        self.data['rows'].append({ 'style': style, 'cells': [{ 'col': 'ticket', 'value': ticket, 'style': '' }] + self.cells })

            
    def process_new_lookups(self, newvalues):
        if 'status' in newvalues:
            if len(newvalues['status']) > 1:
                msg = u' * Some values for the "Status" field do not exist: %s. They will be imported, but will result in invalid status.\n\n'
            else:
                msg = u' * A value for the "Status" field does not exist: %s. It will be imported, but will result in an invalid status.\n\n'
                
            self.message += (msg % u','.join(newvalues['status']))
            del newvalues['status']
            
        if newvalues:
            self.message += ' * Some lookup values are not found and will be added to the possible list of values:\n\n'
            self.message += "   ||'''field'''||'''New values'''||\n"
            for field, values in newvalues.iteritems():                
                self.message += u"   ||%s||%s||\n" % (to_unicode(field.capitalize()), u', '.join(values))
            

    def process_new_users(self, newusers):
        self.message += u' * Some user names do not exist in the system: %s. Make sure that they are valid users.\n' % (u', '.join(newusers))

            
    def end_process(self, numrows):
        notmodifiedcount = numrows - len(self.added) - len(self.modified)
        self.message = 'Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the \'\'\'Execute Import\'\'\' button.\n' + ' * ' + str(numrows) + ' tickets will be imported (' + str(len(self.added)) + ' added, ' + str(len(self.modified)) + ' modified, ' + str(notmodifiedcount) + ' unchanged).\n' + self.message
        self.data['message'] = Markup(self.styles) + wiki_to_html(self.message, self.env, self.req) + Markup('<br/>')

        return 'import_preview.html', self.data, None

