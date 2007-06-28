import re
from trac.core import *
from trac.ticket.roadmap import ITicketGroupStatsProvider, TicketGroupStats
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet


true_values = ('yes', 'true', 'enabled', 'on', '1')


def parse_roadmap_config(rawactions):
    """Given a list of options from [roadmap-groups]"""
    title_attrs = {}
    titles = []
    for option, value in rawactions:
        if option == 'groups':
            titles = value.split(',')
        else:
            parts = option.split('.')
            if len(parts) == 2:
                group = parts[0]
                attr = parts[1]
                if group not in title_attrs:
                    title_attrs[group] = {}
                if attr == 'status':
                    title_attrs[group][attr] = value.split(',')
                elif attr == 'color':
                    title_attrs[group][attr] = value
                elif attr == 'counts':
                    title_attrs[group][attr] = value.lower() in true_values
    groups = []
    for title in titles:
        attrs = title_attrs.get(title)
        status = attrs.get('status', [])
        color = attrs.get('color', '#fff')
        counts = attrs.get('counts', False)
        groups.append((title, status, color, counts))
    return groups


def get_roadmap_config(config):
    """Usually passed self.config, this will return the parsed roadmap
    section.
    """
    # This is the default roadmap used if there is no roadmap section
    # in the ini.  This is the roadmap Trac has historically had.
    default_roadmap = [
        ('groups', 'closed,open'),

        ('closed.status', 'closed'),
        ('closed.color', '#bae0ba'),
        ('closed.counts', 'true'),

        ('open.status', 'new,assigned,reopened'),
        ('open.color', '#fff'),
        ('open.counts', 'false')
    ]
    raw_groups = list(config.options('roadmap-groups'))
    if not raw_groups:
        # Fallback to the default
        raw_groups = default_roadmap
    groups = parse_roadmap_config(raw_groups)
    return groups


class CustomRoadmapTicketGroupStatsProvider(Component):
    implements(ITicketGroupStatsProvider,
               IRequestFilter, IRequestHandler, ITemplateProvider)

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)
        self.groups = get_roadmap_config(self.config)

    # ITicketGroupStatsProvider methods
    def get_ticket_group_stats(self, ticket_ids):
        total_cnt = len(ticket_ids)
        stat = TicketGroupStats('ticket status', 'ticket')
        if total_cnt:
           cursor = self.env.get_db_cnx().cursor()
           id_list = ','.join([str(x)
                               for x in ticket_ids])
           for title, status, color, countsToProg in self.groups:
               status_list = ','.join(["'%s'" % s
                                       for s in status])
               sql = ("SELECT count(1) FROM ticket"
                      " WHERE status IN (%s)"
                      " AND id IN (%s)"
                      % (status_list, id_list))
               cursor.execute(sql)
               count = 0
               for cnt, in cursor:
                   count = cnt
               stat.add_interval(title, int(count), {'status': status},
                                 title, countsToProg)
        stat.refresh_calcs()
        return stat

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info == '/customroadmap/roadmap.css':
            return template, data, 'text/css'
        if (re.match(r'/roadmap/?', req.path_info)
            or re.match(r'/milestone/.*', req.path_info)):
            add_stylesheet(req, '/customroadmap/roadmap.css')
        return template, data, content_type

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/customroadmap/roadmap.css'

    def process_request(self, req):
        data = { 'groups': self.groups }
        return 'roadmap.css', data, 'text/css'

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
