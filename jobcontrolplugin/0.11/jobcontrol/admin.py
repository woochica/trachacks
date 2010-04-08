from trac.core import *
from trac.perm import PermissionSystem
#from trac.ticket.model import AbstractEnum
#from trac.ticket.admin import AbstractEnumAdminPage
from trac.ticket.admin import TicketAdminPanel


from jobcontrol.model import Job
#from clients.events import ClientEvent
from trac.util.datefmt import utc, parse_date, get_date_format_hint, \
                              get_datetime_format_hint
from trac.web.chrome import add_link, add_script

class JobAdminPanel(TicketAdminPanel):
    
    _type = 'jobcontrol'
    _label = ('Job', 'Jobs')

    # TicketAdminPanel methods
    def _render_admin_panel(self, req, cat, page, jobid):
        # Detail view?
        if jobid:
            job = Job(self.env, jobid)
            #events = ClientEvent.select(self.env, client)
            if req.method == 'POST':
                if req.args.get('save'):
                    job.id = req.args.get('id')
                    job.release = req.args.get('release')
                    job.enabled = req.args.get('enabled')
                    job.update()
                    """
                    db = self.env.get_db_cnx()
                    for clev in events:
                      for option in clev.summary_client_options:
                        arg = 'summary-option-%s-%s' % (clev.md5, clev.summary_client_options[option]['md5'])
                        clev.summary_client_options[option]['value'] = req.args.get(arg)
                      for option in clev.action_client_options:
                        arg = 'action-option-%s-%s' % (clev.md5, clev.action_client_options[option]['md5'])
                        clev.action_client_options[option]['value'] = req.args.get(arg)
                      clev.update_options(client, db)
                    db.commit()
                    """
                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            add_script(req, 'common/js/wikitoolbar.js')
            data = {'view': 'detail', 'job': job, } #'events': events}

        else:
            if req.method == 'POST':
                # Add Job
                if req.args.get('add') and req.args.get('id'):
                    job = Job(self.env)
                    job.id = req.args.get('id')
                    job.release = req.args.get('release')
                    job.enabled = False
                    job.insert()
                    req.redirect(req.href.admin(cat, page))

                # Remove jobs
                elif req.args.get('remove') and req.args.get('sel'):
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    if not sel:
                        raise TracError('No job selected')
                    db = self.env.get_db_cnx()
                    for id in sel:
                        job = Job(self.env, id, db=db)
                        job.delete(db=db)
                    db.commit()
                    req.redirect(req.href.admin(cat, page))

                # Set enable/disable jobs 
                elif (req.args.get('enable') or req.args.get('disable'))  and req.args.get('sel'):
                    shouldEnable = req.args.get('enable') is not None
                    sel = req.args.get('sel')
                    sel = isinstance(sel, list) and sel or [sel]
                    db = self.env.get_db_cnx()
                    for id in sel:
                        job = Job(self.env, id, db=db)
                        job.enable( shouldEnable, db=db)
                        self.log.info('%s %s', shouldEnable and 'Enabling' or 'Disabling', id)

                    db.commit()
                    req.redirect(req.href.admin(cat, page))

            data = {'view': 'list',
                    'jobs': Job.select(self.env)
                    }

        return 'admin_jobs.html', data
