"""
sidebar for inputting hours
"""
from api import hours_format # local import
from componentdependencies.interface import IRequireComponents
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.filters.transform import StreamBuffer
from hours import TracHoursPlugin
from ticketsidebarprovider.interface import ITicketSidebarProvider
from ticketsidebarprovider.ticketsidebar import TicketSidebarProvider
from trac.core import *
from trac.ticket import Ticket
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider

class TracHoursRoadmapFilter(Component):
    
    implements(ITemplateStreamFilter, IRequireComponents)

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin]

        ### method for ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        """
        filter the stream for the roadmap (/roadmap)
        and milestones /milestone/<milestone>
        """

        if filename in ('roadmap.html', 'milestone_view.html'):
            trachours = TracHoursPlugin(self.env)

            hours = {}

            milestones = data.get('milestones')
            this_milestone = None

            if milestones is None:
                # /milestone view : only one milestone
                milestones = [ data['milestone'] ]
                this_milestone = milestones[0].name
                find_xpath = "//div[@class='milestone']//h1"
                xpath = "//div[@class='milestone']//div[@class='info']"
            else:
                # /roadmap view
                find_xpath = "//li[@class='milestone']//h2/a"
                xpath = "//li[@class='milestone']//div[@class='info']"


            for milestone in milestones:
                hours[milestone.name] = dict(totalhours=0., 
                                             estimatedhours=0.,)
            
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute("select id from ticket where milestone='%s'" % milestone.name)
                tickets = [i[0] for i in cursor.fetchall()]

                if tickets:
                    hours[milestone.name]['date'] = Ticket(self.env, tickets[0]).time_created
                for ticket in tickets:
                    ticket = Ticket(self.env, ticket)

                    # estimated hours for the ticket
                    try:
                        estimatedhours = float(ticket['estimatedhours'])
                    except (ValueError, TypeError):
                        estimatedhours = 0.
                    hours[milestone.name]['estimatedhours'] += estimatedhours

                    # total hours for the ticket
                    totalhours = trachours.get_total_hours(ticket.id)
                    hours[milestone.name]['totalhours'] += totalhours
                
                    # update date for oldest ticket
                    if ticket.time_created < hours[milestone.name]['date']:
                        hours[milestone.name]['date'] = ticket.time_created
                    # seconds -> hours
                    hours[milestone.name]['totalhours'] /= 3600.


                b = StreamBuffer()
                stream |= Transformer(find_xpath).copy(b).end().select(xpath).append(self.MilestoneMarkup(b, hours, req.href, this_milestone))

        return stream

    class MilestoneMarkup(object):
        """iterator for Transformer markup injection"""
        def __init__(self, buffer, hours, href, this_milestone):
            self.buffer = buffer
            self.hours = hours
            self.href = href
            self.this_milestone = this_milestone
            
        def __iter__(self):
            if self.this_milestone is not None: # for /milestone/xxx
                milestone = self.this_milestone
            else:
                milestone = self.buffer.events[3][1]
            hours = self.hours[milestone]
            estimatedhours = hours['estimatedhours']
            totalhours = hours['totalhours']
            if not (estimatedhours or totalhours):
                return iter([])
            items = []
            if estimatedhours:
                items.append(tag.dt("Estimated Hours:"))
                items.append(tag.dd(str(estimatedhours)))
            date = hours['date']
            link = self.href("hours", milestone=milestone, 
                             from_year=date.year,
                             from_month=date.month,
                             from_day=date.day)
            items.append(tag.dt(tag.a("Total Hours:", href=link)))
            items.append(tag.dd(tag.a(hours_format % totalhours, href=link)))
            return iter(tag.dl(*items))



class TracHoursSidebarProvider(Component):

    implements(ITicketSidebarProvider, IRequireComponents)

    ### method for IRequireComponents
    def requires(self):
        return [TracHoursPlugin, TicketSidebarProvider]


    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        if ticket.id and req.authname and 'TICKET_ADD_HOURS' in req.perm:
            return True
        return False

    def content(self, req, ticket):
        data = { 'worker': req.authname,
                 'action': req.href('hours', ticket.id) }
        return Chrome(self.env).load_template('hours_sidebar.html').generate(**data)


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
