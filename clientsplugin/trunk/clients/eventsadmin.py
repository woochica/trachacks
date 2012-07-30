from trac.core import *
from trac.perm import PermissionSystem
#from trac.ticket.model import AbstractEnum
#from trac.ticket.admin import AbstractEnumAdminPage
from trac.ticket.admin import TicketAdminPanel


from clients.events import ClientEvent, ClientEventsSystem

from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.web.chrome import add_link, add_script


class ClientEventsAdminPanel(TicketAdminPanel):
    
    _type = 'clientevents'
    _label = ('Client Events', 'Client Events')

    # TicketAdminPanel methods
    def get_admin_commands(self):
        return None

    def _render_admin_panel(self, req, cat, page, event):
        # Detail view?
        if event:
            clev = ClientEvent(self.env, event)
            if req.method == 'POST':
                if req.args.get('save'):
                    # Client Events are not saved... just deleted or viewed...
                    for option in clev.summary_options:
                      arg = 'summary-option-%s' % clev.summary_options[option]['md5']
                      clev.summary_options[option]['value'] = req.args.get(arg)
                    for option in clev.action_options:
                      arg = 'action-option-%s' % clev.action_options[option]['md5']
                      clev.action_options[option]['value'] = req.args.get(arg)
                    clev.update_options()
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'event': clev}

        else:
            if req.method == 'POST':
                # Add Client
                if req.args.get('add') and req.args.get('name'):
                    clev = ClientEvent(self.env)
                    clev.name = req.args.get('name')
                    clev.summary = req.args.get('summary')
                    clev.action = req.args.get('action')
                    clev.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove clients
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError('No client event selected')
                    
                    @self.env.with_transaction()
                    def do_delete(db):
                        for name in sel:
                            clev = ClientEvent(self.env, name, db=db)
                            clev.delete(db=db)
                    req.redirect(req.href.admin(cat, page))

            data = {'view': 'list',
                    'events': ClientEvent.select(self.env),
                    'summaries': ClientEventsSystem(self.env).get_summaries(),
                    'actions': ClientEventsSystem(self.env).get_actions()}

        return 'admin_client_events.html', data
