import pkg_resources
import re

from trac.admin.api import IAdminPanelProvider
from trac.core import *
from trac.web.chrome import ITemplateProvider

from model import Availability, Availabilities
from scheduler import Scheduler


class AdminModule(Component):
    """Web administration interface."""

    implements(IAdminPanelProvider, IAdminPanelProvider, ITemplateProvider)

    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        
        yield("scheduling", "Scheduling", "team-avail", "Team Availability")

    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        
        if 'action' in req.args and req.args['action']=='edit':
            return self.edit(req.args['name'])
        if 'action' in req.args and req.args['action']=='delete':
            return self.delete(req.args['name'])
        if 'action' in req.args and req.args['action']=='Save':
            return self.save(req.args)
        if 'action' in req.args and req.args['action']=='Add new':
            return self.add()
        if 'action' in req.args and req.args['action']=='Reset':
            return self.reset()

        return 'admin_availability.html', {"availabilities" : self.availabilities(), "view": "list"}
    
    def get_templates_dirs(self):
        return [pkg_resources.resource_filename('schedulingtools', 'templates')]

    def edit(self, name):
        av = Availability.find(self.env.get_db_cnx(), name)
        self.prepare(av)
        
        return 'admin_availability.html', {"availability" : av, "view": "detail", "date_hint": "YY-MM-DD"}

    def add(self):
        av = Availability()
        av.name = ""
        av.validFrom = None
        av.validUntil = None
        av.weekdays = "12345"
        av.resources = ""
        av.workFrom = "08:00"
        av.workUntil = "16:00"
        self.prepare(av)

        return 'admin_availability.html', {"availability" : av, "view": "detail", "date_hint": "YYYY-MM-DD"}

    def delete(self, name):
        av = Availability.find(self.env.get_db_cnx(), name)
        av.delete(self.env.get_db_cnx())
        scheduler = Scheduler()
        scheduler.schedule(self.env, self.config);
        return 'admin_availability.html', {"availabilities" : self.availabilities(), "view": "list"}

    def save(self, args):
        if args["oldName"] == "":
            key = args["name"]
            av = Availability()
        else:
            key = args["oldName"]
            av = Availability.find(self.env.get_db_cnx(), key)
        av.name = args["name"]
        av.validFrom = args["validFrom"]
        av.validUntil = args["validUntil"]
        av.resources = args["resources"]
        av.weekdays = ""
        self.appendWeekdays(av, args, "1")
        self.appendWeekdays(av, args, "2")
        self.appendWeekdays(av, args, "3")
        self.appendWeekdays(av, args, "4")
        self.appendWeekdays(av, args, "5")
        self.appendWeekdays(av, args, "6")
        self.appendWeekdays(av, args, "0")
        av.workFrom = args["workFrom"]
        av.workUntil = args["workUntil"]
        av.save(self.env.get_db_cnx(), key)
        scheduler = Scheduler()
        scheduler.schedule(self.env, self.config);
        return 'admin_availability.html', {"availabilities" : self.availabilities(), "view": "list"}

    def reset(self):
        Availabilities.reset(self.env.get_db_cnx())
        return 'admin_availability.html', {"availabilities" : self.availabilities(), "view": "list"}

    def availabilities(self):
        availabilities =  Availabilities.get(self.env.get_db_cnx())
        # availabilities = []
        
        for av in availabilities:
            self.prepare(av)
    
        return availabilities
    
    def prepare(self, av):
        av.weekdaysCtrl = []
        self.appendWeekdayCtrl(av, "1", "Monday")
        self.appendWeekdayCtrl(av, "2", "Tuesday")
        self.appendWeekdayCtrl(av, "3", "Wednesday")
        self.appendWeekdayCtrl(av, "4", "Thursday")
        self.appendWeekdayCtrl(av, "5", "Friday")
        self.appendWeekdayCtrl(av, "6", "Saturday")
        self.appendWeekdayCtrl(av, "0", "Sunday")
        av.hrefEdit = "?action=edit&name="+av.name
        av.hrefDelete = "?action=delete&name="+av.name
        
    def appendWeekdayCtrl(self, av, code, label):
        checked = ""
        if av.weekdays.find(code)!=-1:
            checked = "checked='true'"
        av.weekdaysCtrl.append({"title" : label, "control":"<input type='checkbox' name='day%s' %s/>"%(code,checked)})
        
    def appendWeekdays(self, av, args, code):
        if ("day"+code) in args:
            av.weekdays += code