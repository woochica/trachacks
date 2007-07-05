import re
from util import *
from trac.log import logger_factory
from trac.core import *
from trac.web import IRequestHandler
from trac.util import Markup
from trac.web.chrome import add_stylesheet, add_script, \
     INavigationContributor, ITemplateProvider
from trac.web.href import Href

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


    def get_javascript(self, req, ticket, state):
        script = """<script language="javascript" type="text/javascript">
                  function AddEventListener(elem, evt, func, capture){
                    capture = capture || false;
                    if(elem.addEventListener) elem.addEventListener( evt, func, capture);
                    else elem.attachEvent('on'+evt, func);
                    return func;
                  };
                  InitWorklog = function(){
                    var x = document.getElementById('ticket').parentNode;
                    var f = document.createElement('form')
                    f.setAttribute('method', 'POST');
                    f.setAttribute('action', '/worklog')
                    f.setAttribute('class', 'inlinebuttons');
                    var h = document.createElement('input');
                    h.setAttribute('type', 'hidden');
                    h.setAttribute('name', 'ticket');
                    h.setAttribute('value', '""" + str(ticket) + """');
                    f.appendChild(h);
                    var h2 = document.createElement('input');
                    h2.setAttribute('type', 'hidden');
                    h2.setAttribute('name', '__FORM_TOKEN');
                    h2.setAttribute('value', '""" + str(req.incookie['trac_form_token'].value) + """');
                    f.appendChild(h2);
                    var s = document.createElement('input');
                    s.setAttribute('type', 'submit');
                    """
        if state == 0:
            script = script + """s.setAttribute('name', 'startwork');
                    s.setAttribute('value', 'Work on this ticket now');"""
        else:
            script = script + """s.setAttribute('name', 'stopwork');
                    s.setAttribute('value', 'Stop working on this ticket now');"""
        script = script + """f.appendChild(s);

                    x.parentNode.insertBefore(f, x);
                  }
                  AddEventListener(window, 'load', InitWorklog)
                  </script>"""
        return Markup(script)
        
    def get_navigation_items(self, req):
        if req.authname == 'anonymous':
            return
        
        match = re.match(r'/ticket/([0-9]+)$', req.path_info)
        if match:
            ticket = int(match.group(1))

            # Check to see if y
            task = get_latest_task(self.env.get_db_cnx(), req.authname)

            # If we are not working on anything or our latest task is finished we
            # can start working on this task.
            if not task or not task['endtime'] == 0:
                # Display a "Work on Link" button.
                yield 'mainnav', 'ticket-worklog-addon', self.get_javascript(req, ticket, 0)
                return
            
            # We are working on SOMETHING, but not this ticket...
            if task and task['ticket'] == ticket:
                yield 'mainnav', 'ticket-worklog-addon', self.get_javascript(req, ticket, 1)
