from trac.core import *
from trac.perm import PermissionSystem
#from trac.ticket.model import AbstractEnum
#from trac.ticket.admin import AbstractEnumAdminPage
from trac.ticket.admin import TicketAdminPage


from clients import model
from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.web.chrome import add_link, add_script

class ClientAdminPage(TicketAdminPage):
    
    _type = 'clients'
    _label = ('Client', 'Clients')

    # TicketAdminPage methods
    def _render_admin_panel(self, req, cat, page, client):
        # Detail view?
        if client:
            clnt = model.Client(self.env, client)
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
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'client': clnt}

        else:
            if req.method == 'POST':
                # Add Client
                if req.args.get('add') and req.args.get('name'):
                    clnt = model.Client(self.env)
                    clnt.name = req.args.get('name')
                    clnt.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove clients
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError('No client selected')
                    db = self.env.get_db_cnx()
                    for name in sel:
                        clnt = model.Client(self.env, name, db=db)
                        clnt.delete(db=db)
                    db.commit()
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
                    'clients': model.Client.select(self.env),
                    'default': default}

        if self.config.getbool('ticket', 'restrict_owner'):
            perm = PermissionSystem(self.env)
            def valid_owner(username):
                return perm.get_user_permissions(username).get('TICKET_MODIFY')
            data['owners'] = [username for username, name, email
                              in self.env.get_known_users()
                              if valid_owner(username)]
        else:
            data['owners'] = None

        return 'admin_clients.html', data
