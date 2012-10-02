# -*- coding: utf-8 -*-

import re
from genshi import XML
from genshi.filters.transform import Transformer
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_stylesheet, add_script
from trac.wiki.formatter import wiki_to_oneliner

from manager import WorkLogManager
from util import pretty_timedelta

from datetime import datetime


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
            action = 'stop'
            label = 'Stop Work'
        else:
            action = 'start'
            label = 'Start Work'
        
        return '''
            <form id="worklogTicketForm" method="post" action="%s" class="inlinebuttons" onsubmit="return tracWorklog.%s();">
              <input type="hidden" name="source_url" value="%s" />
              <input type="hidden" name="ticket" value="%s" />
              <input type="submit" name="%swork" value="%s" />
            </form>
            <div id="worklogPopup" class="jqmWindow">
              <div style="text-align: right;">
                <span style="text-decoration: underline; color: blue; cursor: pointer;" class="jqmClose">close</span>
              </div>
              <form method="post" action="%s" class="inlinebuttons">
                <input type="hidden" name="source_url" value="%s" />
                <input type="hidden" name="ticket" value="%s" />
                <input id="worklogStoptime" type="hidden" name="stoptime" value="" />
                <fieldset>
                  <legend>Stop work</legend>
                  <div class="field">
                    <fieldset class="iefix">
                      <label for="worklogComment">Optional: Leave a comment about the work you have done...</label>
                      <p><textarea id="worklogComment" name="comment" class="wikitext" rows="6" cols="60"></textarea></p>
                    </fieldset>
                  </div>
                  <div class="field">
                    <label>Override end time</label>
                    <div align="center">
                      <div style="width: 185px;">
                        <div id="worklogStopDate"></div>
                        <br clear="all" />
                        <div style="text-align: right;">
                          &nbsp;&nbsp;@&nbsp;<input id="worklogStopTime" type="text" size="6" />
                        </div>
                      </div>
                    </div>
                  </div>
                  <div style="text-align: right;"><input id="worklogSubmit" type="submit" name="%swork" value="%s" /></div>
                </fieldset>
              </form>
            </div>
            ''' % (req.href.worklog(), action,
                   req.href.ticket(ticket),
                   ticket,
                   action, label,
                   req.href.worklog(),
                   req.href.ticket(ticket),
                   ticket,
                   action, label)


    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match and req.perm.has_permission('WORK_LOG'):
            ticket = int(match.group(1))
            add_stylesheet(req, "worklog/worklogplugin.css")

            add_script(req, 'worklog/jqModal.js')
            add_stylesheet(req, 'worklog/jqModal.css')
            
            add_script(req, 'worklog/ui.datepicker.js')
            add_stylesheet(req, 'worklog/ui.datepicker.css')
            
            add_script(req, 'worklog/jquery.mousewheel.pack.js')
            add_script(req, 'worklog/jquery.timeentry.pack.js')
            
            add_script(req, 'worklog/tracWorklog.js')
            
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
