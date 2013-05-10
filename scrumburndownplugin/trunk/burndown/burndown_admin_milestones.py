from trac.core import *
from trac.util.datefmt import (
    get_date_format_hint, get_datetime_format_hint, parse_date
)

try:  # Trac 0.11 only
    from trac.admin import IAdminPanelProvider
    from trac.util.datefmt import to_timestamp
except ImportError:
    IAdminPanelProvider = None
    to_timestamp = None

import dbhelper


class BurndownMilestonesAdminPanel(Component):
    if IAdminPanelProvider:
        implements(IAdminPanelProvider)

    ### IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('BURNDOWN_ADMIN'):
            yield ('burndown', 'Scrum Burndown Plugin', 'settings', 'Settings')

    def render_admin_panel(self, req, cat, page, milestone):
        req.perm.assert_permission('BURNDOWN_ADMIN')
        db = self.env.get_db_cnx()

        if milestone:
            mil = dbhelper.get_milestone(db, milestone)
            if req.method == 'POST':
                if req.args.get('save'):
                    mil['started'] = None
                    started = req.args.get('started', '')
                    if started:
                        # todo: fill empty dates in
                        mil['started'] = parse_date(started, req.tz)
                        dbhelper.set_startdate_for_milestone(db, mil['name'],
                                                             to_timestamp(mil[
                                                                 'started']))

                    req.redirect(req.href.admin(cat, page))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(cat, page))

            data = {'view': 'detail',
                    'milestone': mil}
        else:
            db = self.env.get_db_cnx()
            milestones = []
            for milestone in dbhelper.get_milestones(db):
                milestones.append(milestone)

            data = {'view': 'list',
                    'milestones': milestones,
                    'default': self.config.get('ticket', 'default_milestone')}

        data.update({
            'date_hint': get_date_format_hint(),
            'datetime_hint': get_datetime_format_hint()
        })

        return 'config.html', data
