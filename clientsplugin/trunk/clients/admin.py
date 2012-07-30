from trac.core import *
from trac.perm import PermissionSystem
#from trac.ticket.model import AbstractEnum
#from trac.ticket.admin import AbstractEnumAdminPage
from trac.ticket.admin import TicketAdminPanel


from clients.model import Client
from clients.events import ClientEvent
from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.web.chrome import add_link, add_script

class ClientAdminPanel(TicketAdminPanel):
    
    _type = 'clients'
    _label = ('Client', 'Clients')

    # TicketAdminPanel methods
    def get_admin_commands(self):
        return None

    def _render_admin_panel(self, req, cat, page, client):
        # Detail view?
        if client:
            clnt = Client(self.env, client)
            events = ClientEvent.select(self.env, client)
            if req.method == 'POST':
                if req.args.get('save'):
                    clnt.name = req.args.get('name')
                    clnt.description = req.args.get('description')
                    clnt.changes_list = req.args.get('changes_list')
                    clnt.changes_period = req.args.get('changes_period')
                    clnt.summary_list = req.args.get('summary_list')
                    clnt.summary_period = req.args.get('summary_period')
                    clnt.default_rate = req.args.get('default_rate')
                    clnt.currency = req.args.get('currency')
                    clnt.update()

                    @self.env.with_transaction()
                    def do_client_event_updates(db):
                      for clev in events:
                        for option in clev.summary_client_options:
                          arg = 'summary-option-%s-%s' % (clev.md5, clev.summary_client_options[option]['md5'])
                          clev.summary_client_options[option]['value'] = req.args.get(arg)
                        for option in clev.action_client_options:
                          arg = 'action-option-%s-%s' % (clev.md5, clev.action_client_options[option]['md5'])
                          clev.action_client_options[option]['value'] = req.args.get(arg)
                        clev.update_options(client, db)

                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'client': clnt, 'events': events}

        else:
            if req.method == 'POST':
                # Add Client
                if req.args.get('add') and req.args.get('name'):
                    clnt = Client(self.env)
                    clnt.name = req.args.get('name')
                    clnt.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove clients
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError('No client selected')

                    @self.env.with_transaction()
                    def do_delete(db):
                        for name in sel:
                            clnt = Client(self.env, name, db=db)
                            clnt.delete(db=db)
                    req.redirect(req.href.admin(cat, page))

                # Set default client
                elif req.args.get('apply'):
                    if req.args.get('default'):
                        name = req.args.get('default')
                        self.log.info('Setting default client to %s', name)
                        self.config.set('ticket', 'default_client', name)
                        self.config.save()
                        req.redirect(req.href.admin(cat, page))

            default = self.config.get('ticket', 'default_client')
            data = {'view': 'list',
                    'clients': Client.select(self.env),
                    'default': default}

        return 'admin_clients.html', data
