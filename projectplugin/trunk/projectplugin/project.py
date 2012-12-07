from genshi.filters import Transformer
from genshi.path import Path
from trac.admin.api import IAdminPanelProvider
from trac.core import Component, implements
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.ticket.api import ITicketChangeListener
from trac.util.translation import domain_functions
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet


_, tag_, N_, add_domain = domain_functions('projectplugin', '_', 'tag_', 'N_', 'add_domain')

class ProjectAdmin(Component):
    """Adds project number to ticket.
    
    User which have right `CONTROLLER_ADMIN` (or `TRAC_ADMIN`) can edit list of default project numbers in admin pane.
    
    Editing project number manually:
    - when creating a ticket, manually typed project numbers will be '''skipped''' !
    """
    implements(IAdminPanelProvider, ITemplateProvider, ITicketChangeListener, IPermissionRequestor, IRequestFilter)
    # ITemplateStreamFilter , IRequestHandler, ITicketManipulator

    changed_fields = ['type', 'milestone']

    #===========================================================================
    # TODO: maybe using class CustomField from settings.py
    #===========================================================================
    def _init_config(self):
        section = 'ticket-custom'
        fld_name = 'projectplugin'

        if self.config and not self.config.get(section, fld_name):
            self.log.debug("adding custom-ticket %s" % fld_name)
            self.config.set(section, fld_name, 'text')
            self.config.set(section, fld_name + '.label', 'Project')
            self.config.set(section, fld_name + '.order', '40')
            self.config.set(section, fld_name + '.value', '')
            self.config.save()
            self.log.info("custom-ticket fields added to trac.ini")

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename #@UnresolvedImport
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename #@UnresolvedImport
        return [('pp_htdocs', resource_filename(__name__, 'htdocs'))]

    # IPermissionRequestor
    def get_permission_actions(self):
        yield ("CONTROLLER_ADMIN")

    def checkPermissions(self, req):
        for permission in ("TRAC_ADMIN", "CONTROLLER_ADMIN"):
            if permission in PermissionSystem(self.env).get_user_permissions(req.authname):
                return True
        return False

#===============================================================================
# ITicketChangeListener
#===============================================================================
    def ticket_created(self, ticket):
        self._save_project_no(ticket, self.changed_fields)
        return

    def ticket_changed(self, ticket, comment, author, old_values):
        if 'projectplugin' in old_values:
            return

        flds = []
        for cf in self.changed_fields:
            if cf in old_values:
                flds.append(cf)
        self._save_project_no(ticket, flds)
        return

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        return

    def pre_process_request(self, req, handler):
        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, data, content_type):
        if template == 'ticket.html':
            self._init_config()
            if not self.checkPermissions(req):
                add_stylesheet(req, 'pp_htdocs/prj_style.css')
        return template, data, content_type

    # overridden from IAdminPanelProvider
    def get_admin_panels(self, req):
        """Return a list of available admin panels.
        
        The items returned by this function must be tuples of the form
        `(category, category_label, page, page_label)`.
        """
        # TODO: add new permission !!!
        if req.perm.has_permission('TRAC_ADMIN') or req.perm.has_permission("CONTROLLER_ADMIN"):
            yield ('ticket', _('Ticket System'), 'projectplugin', _('Project'))

    # overridden from IAdminPanelProvider
    def render_admin_panel(self, req, category, page, path_info):
        """Process a request for an admin panel.
        
        This function should return a tuple of the form `(template, data)`,
        where `template` is the name of the template to use and `data` is the
        data to be passed to the template.
        """
        errors = []
        if req.args and 'projectname' in req.args:
            errors = self._save({'projectname': req.args['projectname'],
                        'milestone': req.args['milestone'],
                        'type': req.args['type'] })

        return self._print_view(errors)


    def _save_project_no(self, ticket, changed_fields):
        """Save project number to corresponding ticket. """
        projects, max_order = self._get_projects()
        project_no = self.config.get('project-plugin', 'default-project')

        for prj in projects:
            if prj['field'] in changed_fields:
                val = ticket.get_value_or_default(prj['field'])
                if val == prj['value']:
                    project_no = prj['project']
                    break

        try:
            result = self.env.db_query("SELECT value FROM ticket_custom"
                                       " WHERE ticket=%s"
                                       " AND name='projectplugin'" % (ticket.id))
            sql_type = "inserted"
            for row in result:
                if row[0] and row[0] == project_no:
                    self.log.info('project no %s already committed for ticket %s' % (project_no, ticket.id,))
                    return []
                else:
                    sql_type = "updated"
            if sql_type == "inserted":
                self.env.db_transaction("INSERT INTO ticket_custom (ticket, name, value)"
                                        " VALUES(%s, 'projectplugin', '%s') " % (ticket.id, project_no))
            else:
                self.env.db_transaction("UPDATE ticket_custom "
                                        " SET value = '%s'"
                                        " WHERE ticket = %s"
                                        " AND name='projectplugin'" %
                                        (project_no, ticket.id))

            self.log.info('%s project no %s for ticket %s' % (sql_type, project_no, ticket.id,))
            return []
        except Exception, e:
            self.log.error ("Error executing SQL Statement \n %s" % (e))
            return ['projectplugin', e]

    def _save(self, new_project):
        """Save project to config file (`trac.ini`). """
        if new_project:
            if not new_project['type'] and not new_project['milestone']:
                return ['Type or milestone is not set; one of it has to be selected']
            elif not new_project['projectname']:
                return ['Project name is not set, but mandatory']
        else:
            return []

        projects, max_order = self._get_projects()
        #=======================================================================
        # # enhencement: make list editable
        # if new_project.has_key('order'):
        #    for prj in projects:
        #        if prj['order'] == new_project['order']:
        #            # project already exists, pls update in config
        #            pass
        #=======================================================================
        fld_name = None
        if new_project['type']:
            fld_name = 'type'
        elif new_project['milestone']:
            fld_name = 'milestone'

        field = 'order.%s.%s' % (max_order, fld_name)
        value = '%s;%s' % (new_project['type'] or new_project['milestone'], new_project['projectname'])
        self.log.info('saved new default project number: field: %s, project: %s' % (field, value))
        self.config.set('project-plugin', field, value)
        self.config.save()
        return []

    def _get_projects(self):
        if 'project-plugin' in self.config:
            entries = []
            max_order = 1
            for optname, value in self.config.options('project-plugin'):
                row_fld = optname.split('.')
                row_val = value.split(';')
                if len(row_fld) == 3 and len(row_val) == 2:
                    entries.append({'order': row_fld[1],
                           'field': row_fld[2],
                           'value': row_val[0],
                           'project': row_val[1]})
            max_order = len(entries) + 1
            if max_order > 0:
                sorted(entries, key=lambda k: k['order'])
            return entries, max_order
        else:
            return [], 1

    def _print_view(self, errors):
        projects, max_order = self._get_projects()
        data = {'ticket_types': self._get_enums('ticket_type'),
                'milestones': self._get_milestones(),
                'projects': projects,
                'errors': errors }

        return 'project-admin.html', data

    def _get_enums(self, enum_name):
        if not enum_name:
            return []

        result = self.env.db_query("SELECT type, name, value FROM enum"
                                   " WHERE type='%s' ORDER BY value" ,
                                   (enum_name))
        sqlResult = []

        try:
            for row in result:
                sqlResult.append({'type': row[0], 'name': row[1], 'value': row[2]})
        except Exception, e:
            self.log.error ("Error executing SQL Statement \n %s" % (e))

        return sqlResult

    def _get_milestones(self):
        sqlResult = []
        try:
            result = self.env.db_query("SELECT name FROM milestone"
                                       " WHERE completed=0 ORDER BY name")
            for row in result:
                sqlResult.append(row[0])
        except Exception, e:
            self.log.error ("Error executing SQL Statement \n %s" % (e))

        return sqlResult
