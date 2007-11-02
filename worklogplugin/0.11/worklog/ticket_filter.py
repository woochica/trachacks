import re
from util import *
from trac.core import *
from trac.web.api import ITemplateStreamFilter
from trac.wiki import wiki_to_oneliner

from manager import WorkLogManager
from util import pretty_timedelta

from genshi import XML
from genshi.builder import tag
from genshi.filters.transform import Transformer 

class WorkLogTicketAddon(Component):
    implements(ITemplateStreamFilter)
    
    def __init__(self):
        pass
    
    def get_task_markup(self, req, ticket, task):
        if not task:
            return ''
        
        ticket_text = 'ticket #' + str(task['ticket'])
        if task['ticket'] == ticket:
            ticket_text = 'this ticket'
        timedelta = pretty_timedelta(datetime.fromtimestamp(task['starttime']), None);
        
        return '<li>%s</li>' % wiki_to_oneliner('You have been working on %s for %s' % (ticket_text, timedelta), self.env, req=req)
    
    
    def get_ticket_markup(self, who, since):
        timedelta = pretty_timedelta(datetime.fromtimestamp(since), None);
        return '<li>%s has been working on this ticket for %s</li>' % (who, timedelta)
    
    
    def get_ticket_markup_noone(self):
        return '<li>Nobody is working on this ticket</li>'
    
    
    def get_button_markup(self, req, ticket, stop=False):
        if stop:
            button = '''
                <span id="worklog_comment">Comment:
                <input type="text" size="50" name="comment" /></span>
                <input type="submit" name="stopwork" value="Stop Work" />
                '''
        else:
            button = '''
                <input type="submit" name="startwork" value="Start Work" />
                '''
        
        return '''
            <form method="post" action="%s" class="inlinebuttons">
              <input type="hidden" name="source_url" value="%s" />
              <input type="hidden" name="ticket" value="%s" />
              %s
            </form>
            ''' % (req.href.worklog(), 
                   req.href.ticket(ticket), 
                   ticket,
                   button)


    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match:
            ticket = int(match.group(1))
            
            mgr = WorkLogManager(self.env, self.config, req.authname)
            task_markup = ''
            if req.authname != 'anonymous':
                task = mgr.get_active_task()
                if task:
                    task_markup = self.get_task_markup(req, ticket, task)

            who,since = mgr.who_is_working_on(ticket)
            ticket_markup = ''
            if who:
                # If who == req.authname then we will have some text from above.
                if who != req.authname:
                    ticket_markup = self.get_ticket_markup(who, since)
            else:
                ticket_markup = self.get_ticket_markup_noone()
            
            button_markup = ''
            if req.authname != 'anonymous':
                if mgr.can_work_on(ticket):
                    # Display a "Work on Link" button.
                    button_markup = self.get_button_markup(req, ticket)
                elif task and task['ticket'] == ticket:
                    # We are currently working on this, so display the stop button...
                    button_markup = self.get_button_markup(req, ticket, True)
            
            # User's current task information
            html = XML('''
              <fieldset class="workloginfo">
                <legend>Work Log</legend>
                %s
                <ul>
                  %s
                  %s
                </ul>
              </fieldset>
              ''' % (button_markup, task_markup, ticket_markup))
            stream |= Transformer('.//div[@id="ticket"]').before(html)
        return stream
