# TicketModifiedFiles plugin
# This software is licensed as described in the file COPYING.txt, which you
# should have received as part of this distribution.

import re

import genshi.filters

from trac.core import *
from trac.ticket.model import Ticket
from trac.web import IRequestHandler
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script

#WARNING: genshi.filters.Transformer requires Genshi 0.5+
from genshi.filters import Transformer
from genshi.builder import tag

class TicketModifiedFilesPlugin(Component):
    implements(IRequestHandler, IRequestFilter, ITemplateProvider, ITemplateStreamFilter)
    
    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/modifiedfiles/([0-9]+)$', req.path_info)
        if match:
            req.args['id'] = match.group(1)
            return True
    
    def process_request(self, req):
        #Retrieve the information needed to display in the /modifiedfiles/ page
        (id, files, deletedfiles, ticketsperfile, filestatus, conflictingtickets, ticketisclosed, revisions) = self.__process_ticket_request(req)
        #Pack the information to send to the html file
        data = {'ticketid':id, 'files':files, 'deletedfiles':deletedfiles, 'ticketsperfile':ticketsperfile, 'filestatus':filestatus, 'conflictingtickets':conflictingtickets, 'ticketisclosed':ticketisclosed, 'revisions':revisions}
        #Add the custom stylesheet
        add_stylesheet(req, 'common/css/timeline.css')
        add_stylesheet(req, 'tmf/css/ticketmodifiedfiles.css')
        add_script(req, 'tmf/js/ticketmodifiedfiles.js')
        return 'ticketmodifiedfiles.html', data, None
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match:
            data['modifiedfiles'] = int(match.group(1))
        return template, data, content_type

    # ITemplateProvider methods
    # Used to add the plugin's templates and htdocs 
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('tmf', resource_filename(__name__, 'htdocs'))]
    
    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if 'modifiedfiles' in data:
            #If there are conflicting tickets, display a warning message
            #Only show the message when the current ticket is not closed
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT status FROM ticket WHERE id=" + str(req.args.get('id')))
            for status, in cursor:
                if status != "closed":
                    numconflictingtickets = self.__process_ticket_request(req, True)
                    if numconflictingtickets > 0:
                        text = " There "
                        if numconflictingtickets == 1: text += "is one ticket that is"
                        else: text += "are " + str(numconflictingtickets) + " tickets that are"
                        text += " in conflict with this one!"
                        stream |= Transformer("//div[@id='content']/div[@id='changelog']").before(tag.p(tag.strong("Warning:"), text, style='background: #def; border: 2px solid #00d; padding: 3px;'))
            
            #Display the link to this ticket's modifiedfiles page
            stream |= Transformer("//div[@id='content']/div[@id='changelog']").before(
                       tag.p(
                             'Have a look at the ',
                             tag.a("list of modified files", href="../modifiedfiles/" + str(data["modifiedfiles"])),
                             ' related to this ticket.'
                             )
                       )
        return stream

    # Internal methods
    def __process_ticket_request(self, req, justnumconflictingtickets = False):
        id = int(req.args.get('id'))
        req.perm('ticket', id, None).require('TICKET_VIEW')
        
        #Check if the ticket exists
        Ticket(self.env, id, version=None)
        
        #Get the list of modified files
        files = []
        revisions = []
        ticketsperfile = {}
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        #Retrieve all the revisions which's messages contain "#<TICKETID>"
        cursor.execute("SELECT rev, author, message FROM revision WHERE message LIKE '%#" + str(id) + "%'")
        for rev, author, message, in cursor:
            #Filter out non-related revisions.
            #for instance, you are lookink for #19, so you don't want #190, #191, #192, etc. to interfere
            #To filter, check what the eventual char after "#19" is.
            #If it's a number, we dont' want it (validrevision = False), but if it's text, keep this revision
            validrevision = True
            tempstr = message.split("#" + str(id), 1)
            if len(tempstr[1]) > 0:
                try:
                    int(tempstr[1][0])
                    validrevision = False
                except: pass
                
            if validrevision:
                cursor2 = db.cursor()
                cursor2.execute("SELECT path FROM node_change WHERE rev=" + rev)
                revisions.append((rev, author))
                for path, in cursor2:
                    files.append(path)
        
        #Remove duplicated values
        files = self.__remove_duplicated_elements_and_sort(files)
        
        filestatus = {}
        #Get the last status of each file
        for file in files:
            cursor.execute("SELECT change_type FROM node_change WHERE path='" + file + "' ORDER BY 1*rev DESC LIMIT 1")
            for change_type, in cursor:
                filestatus[file] = change_type
        
        #Get the list of conflicting tickets per file
        for file in files:
            tempticketslist = []
            cursor.execute("SELECT message FROM revision WHERE rev in (SELECT rev FROM node_change WHERE path='" + file + "')")
            for message, in cursor:
                #Extract the ticket number
                match = re.search(r'#([0-9]+)', message)
                if match:
                    ticket = int(match.group(1))
                    #Don't add yourself
                    if ticket != id:
                        tempticketslist.append(ticket)
            tempticketslist = self.__remove_duplicated_elements_and_sort(tempticketslist)
            ticketsperfile[file] = []
            
            #Keep only the active tickets
            for ticket in tempticketslist:
                cursor.execute("SELECT status FROM ticket WHERE id=" + str(ticket))
                for status, in cursor:
                    if status != "closed":
                        ticketsperfile[file].append(ticket)
        
        #Get the global list of conflicting tickets
        #Only if the ticket is not already closed
        conflictingtickets=[]
        cursor.execute("SELECT status FROM ticket WHERE id=" + str(req.args.get('id')))
        for status, in cursor:
            if status != "closed":
                ticketisclosed = False
                for fn, relticketids in ticketsperfile.items():
                    for relticketid in relticketids:
                        cursor.execute("SELECT summary, status, owner FROM ticket WHERE id=" + str(relticketid))
                        for summary, status, owner, in cursor:
                            conflictingtickets.append((relticketid, summary, status, owner))
        
                #Remove duplicated values
                conflictingtickets = self.__remove_duplicated_elements_and_sort(conflictingtickets)
            else:
                ticketisclosed = True
        
        #Separate the deleted files from the others
        deletedfiles = []
        for file in files:
            if filestatus[file] == "D":
                deletedfiles.append(file)
        for deletedfile in deletedfiles:
            files.remove(deletedfile)
        
        #Return only the number of conflicting tickets (if asked for)
        if justnumconflictingtickets:
            return len(conflictingtickets)
        
        #Return all the needed information
        return (id, files, deletedfiles, ticketsperfile, filestatus, conflictingtickets, ticketisclosed, revisions)
    
    def __remove_duplicated_elements_and_sort(self, list):
        d = {}
        for x in list: d[x]=1
        return sorted(d.keys())