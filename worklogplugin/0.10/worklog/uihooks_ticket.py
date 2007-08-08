import re
from util import *
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, INavigationContributor
from trac.web.href import Href
from manager import WorkLogManager
from util import pretty_timedelta

class WorkLogTicketAddon(Component):
    implements(INavigationContributor)
    
    def __init__(self):
        pass
    
     # INavigationContributor methods
    def get_active_navigation_item(self, req):
    
        if re.search('ticket', req.path_info):
            return 'ticket-worklog-addon'
        else:
            return ''

    def get_task_js(self, req, ticket, task):
        script = """
  li_task = document.createElement('li');
  ul.appendChild(li_task);
  li_task.appendChild(document.createTextNode('You have been working on '));"""
        if task:
            if ticket == task['ticket']:
                script += """
  li_task.appendChild(document.createTextNode('this ticket'));"""
            else:
                script += """
  li_task.appendChild(document.createTextNode('ticket '));
  var a = document.createElement('a');
  a.setAttribute('href', '""" + req.href.ticket(task['ticket']) + """');
  a.setAttribute('title', '""" + task['summary'].replace("'", "\\'") + """');
  a.appendChild(document.createTextNode('#""" + str(task['ticket']) + """'));
  li_task.appendChild(a);"""

            timedelta = pretty_timedelta(datetime.fromtimestamp(task['starttime']), None);
            script += """
  li_task.appendChild(document.createTextNode(' for """ + timedelta + """'));"""
        return script;


    def get_ticket_js(self, who, since):
        timedelta = pretty_timedelta(datetime.fromtimestamp(since), None);
        script = """
  li_tctk = document.createElement('li');
  ul.appendChild(li_tctk);
  li_tctk.appendChild(document.createTextNode('""" + who + """ has been working on this ticket for """ + timedelta + """'));"""
        return script;

    def get_ticket_js_noone(self):
        script = """
  li_tctk = document.createElement('li');
  ul.appendChild(li_tctk);
  li_tctk.appendChild(document.createTextNode('Nobody is working on this ticket.'));"""
        return script;


    def get_button_js(self, req, ticket, stop=False):
        script = """
  var f = document.createElement('form');
  d.appendChild(f);
  f.setAttribute('method', 'POST');
  f.setAttribute('action', '""" + req.href.worklog() + """')
  f.setAttribute('class', 'inlinebuttons');
  
  var h_url = document.createElement('input');
  h_url.setAttribute('type', 'hidden');
  h_url.setAttribute('name', 'source_url');
  h_url.setAttribute('value', location.pathname);
  f.appendChild(h_url);
  
  var h = document.createElement('input');
  h.setAttribute('type', 'hidden');
  h.setAttribute('name', 'ticket');
  h.setAttribute('value', '""" + str(ticket) + """');
  f.appendChild(h);
  
  var h2 = document.createElement('input');
  h2.setAttribute('type', 'hidden');
  h2.setAttribute('name', '__FORM_TOKEN');
  h2.setAttribute('value', '""" + str(req.incookie['trac_form_token'].value) + """');
  f.appendChild(h2);"""
  
        if stop:
            script += """
  var s_comment_label = document.createElement('span');
  s_comment_label.id = 'worklog_comment';
  s_comment_label.innerHTML = 'Comment: ';
  f.appendChild(s_comment_label);
  
  var s_comment = document.createElement('input');
  s_comment.type = 'text';
  s_comment.size = '50';
  s_comment.name = 'comment';
  f.appendChild(s_comment);"""
  
        script += """
  var s = document.createElement('input');
  s.setAttribute('type', 'submit');"""
        if stop:
            script += """
  s.setAttribute('name', 'stopwork');
  s.setAttribute('value', 'Stop Work');"""
        else:
            script += """
  s.setAttribute('name', 'startwork');
  s.setAttribute('value', 'Start Work');"""
        script += """
  f.appendChild(s);"""
        return script


    def get_javascript(self, task_js='', ticket_js='', button_js=''):
        script = """
<script language=\"javascript\" type=\"text/javascript\">
function wlAddEventListener(elem, evt, func, capture)
{
  capture = capture || false;
  if (elem.addEventListener)
    elem.addEventListener(evt, func, capture);
  else
    elem.attachEvent('on'+evt, func);
    return func;
}

InitWorklog = function()
{
  var x = document.getElementById('ticket').parentNode;
  var d = document.createElement('fieldset');
  d.setAttribute('class', 'workloginfo');
  l = document.createElement('legend')
  l.appendChild(document.createTextNode('Work Log'));
  d.appendChild(l);
  """ + button_js + """
  ul = document.createElement('ul');
  d.appendChild(ul);
  """ + task_js + ticket_js + """  
  x.parentNode.insertBefore(d, x);
}
wlAddEventListener(window, 'load', InitWorklog)
</script>
"""
        return Markup(script)
        
    def get_navigation_items(self, req):
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match:
            add_stylesheet(req, "worklog/worklogplugin.css")
            ticket = int(match.group(1))

            mgr = WorkLogManager(self.env, self.config, req.authname)
            task_js = ''
            if req.authname != 'anonymous':
                task = mgr.get_active_task()
                if task:
                    task_js = self.get_task_js(req, ticket, task)

            who,since = mgr.who_is_working_on(ticket)
            ticket_js = ''
            if who:
                # If who == req.authname then we will have some text from above.
                if who != req.authname:
                    ticket_js = self.get_ticket_js(who, since)
            else:
                ticket_js = self.get_ticket_js_noone()
            
            button_js = ''
            if req.authname != 'anonymous':
                if mgr.can_work_on(ticket):
                    # Display a "Work on Link" button.
                    button_js = self.get_button_js(req, ticket)
                elif task and task['ticket'] == ticket:
                    # We are currently working on this, so display the stop button...
                    button_js = self.get_button_js(req, ticket, True)

            yield 'mainnav', 'ticket-worklog-addon', self.get_javascript(task_js, ticket_js, button_js)
