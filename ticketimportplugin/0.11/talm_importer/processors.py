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
from trac.wiki import wiki_to_html


class ImportProcessor(object):
    def __init__(self, env, req, filename, tickettime):
        self.env = env
        self.req = req
        self.filename = filename
        self.modifiedcount = 0
        self.notmodifiedcount = 0
        self.added = 0

        # TODO: check that the tickets haven't changed since preview
        self.tickettime = tickettime
        
        # Keep the db to commit it all at once at the end
        self.db = self.env.get_db_cnx()
        self.missingemptyfields = None
        self.missingdefaultedfields = None
        self.computedfields = None

    def start(self, importedfields, reconciliate_by_owner_also):
        pass

    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.missingemptyfields = missingemptyfields
        self.missingdefaultedfields = missingdefaultedfields
        self.computedfields = computedfields

    def process_notimported_fields(self, notimportedfields):
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

    def process_cell(self, column, cell):
        cell = unicode(cell)
        # this will ensure that the changes are logged, see model.py Ticket.__setitem__
        self.ticket[column.lower()] = cell

    def end_process_row(self):
        try:
            # 'when' is a datetime in 0.11, and an int in 0.10.
            # if we have trac.util.datefmt.to_datetime, we're likely with 0.11
            from trac.util.datefmt import to_datetime
            tickettime = to_datetime(self.tickettime)
        except ImportError:
            tickettime = self.tickettime
                
        if self.ticket.id == None:
            for f in self.missingemptyfields:
                if self.ticket.values.has_key(f) and self.ticket[f] == None:
                    self.ticket[f] = ''
            for f in self.computedfields:
                 if self.computedfields[f] != None and self.computedfields[f]['set']:
                     self.ticket[f] = self.computedfields[f]['value']

            self.added += 1
            self.ticket.insert(when=tickettime, db=self.db)
        else: 
            message = "Batch update from file " + self.filename
            if self.ticket.is_modified():
                self.modifiedcount += 1
                self.ticket.save_changes(get_reporter_id(self.req), message, when=tickettime, db=self.db) # TODO: handle cnum, cnum = ticket.values['cnum'] + 1)
            else:
                self.notmodifiedcount += 1

        self.ticket = None

    def process_new_lookups(self, newvalues):
        for field, names in newvalues.iteritems():
            if names == []:
                continue
            if field == 'component':
                class CurrentLookupEnum(model.Component):
                    pass
            elif field == 'milestone':
                class CurrentLookupEnum(model.Milestone):
                    pass
            elif field == 'version':
                class CurrentLookupEnum(model.Version):
                    pass
            else:
                class CurrentLookupEnum(model.AbstractEnum):
                    # here, you shouldn't put 'self.' before the class field.
                    type = field

            for name in names:
                lookup = CurrentLookupEnum(self.env, db=self.db)
                lookup.name = name
                lookup.insert()

    def process_new_users(self, newusers):
        pass
            
    def end_process(self, numrows):
        self.db.commit()

        self.req.hdf['title'] = 'Import completed'
        self.req.hdf['report.title'] = self.req.hdf['title'].lower()

        message = 'Successfully imported ' + str(numrows) + ' tickets (' + str(self.added) + ' added, ' + str(self.modifiedcount) + ' modified, ' + str(self.notmodifiedcount) + ' unchanged).'

        self.req.hdf['report.description'] = Markup("<style type=\"text/css\">#report-notfound { display:none; }</style>\n") + wiki_to_html(message, self.env, self.req)

        self.req.hdf['report.numrows'] = 0
        self.req.hdf['report.mode'] = 'list'
        return 'report.cs', None
    

class PreviewProcessor(object):
    
    def __init__(self, env, req):
        self.env = env
        self.req = req
        self.ticket = None
        self.modified = 0
        self.temphdf = None
        self.styles = ''
        self.duplicatessumaries = []
        self.modifiedcount = 0
        self.notmodifiedcount = 0
        self.added = 0

    def start(self, importedfields, reconciliate_by_owner_also):
        self.req.hdf['title'] = 'Preview Import'
        self.req.hdf['report.title'] = self.req.hdf['title'].lower()

        self.message = ''

        if 'ticket' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'ticket\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n' 
        elif 'id' in [f.lower() for f in importedfields]:
            self.message += ' * A \'\'\'id\'\'\' column was found: Existing tickets will be updated with the values from the file. Values that are changing appear in italics in the preview below.\n' 
        else:
            self.message += ' * A \'\'\'ticket\'\'\' column was not found: tickets will be reconciliated by summary' + (reconciliate_by_owner_also and ' and by owner' or '') + '. If an existing ticket with the same summary' + (reconciliate_by_owner_also and ' and the same owner' or '') + ' is found, values that are changing appear in italics in the preview below. If no ticket with same summary ' + (reconciliate_by_owner_also and ' and same owner' or '') + 'is found, the whole line appears in italics below, and a new ticket will be added.\n' 
                                
        idx = 0
        prefix = 'report.headers.%d' % idx
        self.req.hdf['%s.real' % prefix] = 'ticket'
        self.req.hdf[prefix] = 'ticket'
        idx = idx + 1
        # we use one more color to set a style for all fields in a row... the CS templates happens 'color' + color + '-odd'
        self.styles = "<style type=\"text/css\">\n.ticket-imported, .modified-ticket-imported { width: 40px; }\n"
        self.styles += ".color-new-odd td, .color-new-even td, .modified-ticket-imported"
        for col in importedfields:
            if col.lower() != 'ticket' and col.lower() != 'id':
                title=col.capitalize()
                prefix = 'report.headers.%d' % idx
                self.req.hdf['%s.real' % prefix] = col
                self.req.hdf[prefix] = title
                self.styles += ", .modified-%s" % col
                idx = idx + 1
        self.styles += " { font-style: italic; }\n"
        self.styles += "</style>\n"

    # This could be simplified...
    def process_missing_fields(self, missingfields, missingemptyfields, missingdefaultedfields, computedfields):
        self.message += ' * Some Trac fields are not present in the import. They will default to:\n\n'
        self.message += "   ||'''field'''||'''Default value'''||\n"
        if missingemptyfields != []:
            self.message += '   ||' + ', '.join([x.capitalize() for x in missingemptyfields]) + '||' + "''(Empty value)''" + '||\n'
            
        if missingdefaultedfields != []:
            for f in missingdefaultedfields:
                self.message += '   ||' + f.capitalize() + '||' + str(computedfields[f]['value']) + '||\n'

        self.message += '(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n'

    def process_notimported_fields(self, notimportedfields):
        self.message += ' * Some fields will not be imported because they don\'t exist in Trac: ' + ', '.join([x and x or "''(empty name)''" for x in notimportedfields])  + '.\n'

    def start_process_row(self, row_idx, ticket_id):
        from ticket import PatchedTicket
        self.ticket = None
        self.row_idx = row_idx
        self.temphdf = []
        if ticket_id > 0:
            # existing ticket. Load the ticket, to see which fields will be modified
            self.ticket = PatchedTicket(self.env, ticket_id)
            

    def process_cell(self, column, cell):
        value = {}

        if self.ticket and not (self.ticket.values.has_key(column) and self.ticket[column] == cell):
            prefix = 'report.items.%d.modified-%s' % (self.row_idx, unicode(column))
            self.modified = 1
        else:
            prefix = 'report.items.%d.%s' % (self.row_idx, unicode(column))

        if column in ('time', 'date', 'changetime', 'created', 'modified'):
            # TODO: TEST THIS, THIS IS NOT TESTED
            if cell != 'None':
                value[column] = format_datetime(cell)
                
        self.temphdf += [ {prefix: cell} ]
        for key in value.keys():
            self.temphdf += [ {prefix + '.' + key: value[key] }]

    def end_process_row(self):
        if self.ticket:
            if self.modified:
                self.modifiedcount += 1
            else:
                self.notmodifiedcount += 1
        else: 
            self.added += 1

        prefix = 'report.items.%d.' % self.row_idx
        if self.ticket:
            if self.modified:
                self.req.hdf[prefix + 'modified-ticket-imported'] = str(self.ticket.id)
            else:
                self.req.hdf[prefix + 'ticket-imported'] = str(self.ticket.id)
        else:
            self.req.hdf[prefix + "__color__"] = '-new'
            self.req.hdf[prefix + "__color__.hidden"] = 1
            self.req.hdf[prefix + 'ticket-imported'] = '(new)'

        # We have to do a complex gymnastic because the template relies on the *order* of the values in the list !!!
        for item in self.temphdf:
            for k, v in item.iteritems():
                self.req.hdf[k] = v
        self.temphdf = None

        self.modified = 0    
        self.ticket = None
            
    def process_new_lookups(self, newvalues):
        self.message += ' * Some lookup values are not found and will be added to the possible list of values:\n\n'
        self.message += "   ||'''field'''||'''New values'''||\n"
        for field, values in newvalues.iteritems():
            if values == []:
                continue
            self.message += "   ||" + field.capitalize() + "||" + ', '.join(values) + "||\n"
            

    def process_new_users(self, newusers):
        self.message += ' * Some user names do not exist in the system: ' + ', '.join(newusers) + '. Make sure that they are valid users.\n'
            
    def end_process(self, numrows):
        self.message = 'Scroll to see a preview of the tickets as they will be imported. If the data is correct, select the \'\'\'Execute Import\'\'\' button.\n' + ' * ' + str(numrows) + ' tickets will be imported (' + str(self.added) + ' added, ' + str(self.modifiedcount) + ' modified, ' + str(self.notmodifiedcount) + ' unchanged).\n' + self.message
        self.req.hdf['report.description'] = Markup(self.styles) + wiki_to_html(self.message, self.env, self.req) + Markup('<br/><form action="importer" method="post"><input type="hidden" name="action" value="import" /><div class="buttons"><input type="submit" name="cancel" value="Cancel" /><input type="submit" value="Execute import" /></div></form>')

        self.req.hdf['report.numrows'] = numrows
        self.req.hdf['report.mode'] = 'list'
        return 'report.cs', None

if __name__ == '__main__': 
    import doctest
    testfolder = __file__
    doctest.testmod()

