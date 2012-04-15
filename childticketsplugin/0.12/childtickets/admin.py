from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import add_notice, add_warning, add_stylesheet
from trac.util.text import exception_to_unicode
from trac.util.translation import _, get_available_locales, ngettext


def _save_config(config, req, log):
    """Try to save the config, and display either a success notice or a
    failure warning.
    """
    try:
        config.save()
        add_notice(req, _('Your changes have been saved.'))
    except Exception, e:
        log.error('Error writing to trac.ini: %s', exception_to_unicode(e))
        add_warning(req, _('Error writing to trac.ini, make sure it is '
                           'writable by the web server. Your changes have not '
                           'been saved.'))


class ChildTicketsAdminPanel(Component):

    implements(IAdminPanelProvider, ITemplateProvider)


    # Class variables 'static'
    HEADERS = ('type', 'status', 'owner', 'summary', 'priority', 'component', 'version', 'resolution', 'milestone', 'parent', 'keywords', 'reporter', 'cc')
    INHERITED = ('summary', 'priority', 'component', 'version', 'milestone', 'keywords', 'cc')

    # IAdminPanelProvidermethods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('childticketsplugin', _('Child Tickets Plugin'), 'types', _('Parent Types'))

    def render_admin_panel(self, req, cat, page, parenttype):

        # Only for trac admins.
        req.perm.require('TRAC_ADMIN')

        for t in self._types():
            x = self.config.getlist('childtickets', 'parent.%s.table_headers' % t, default=['rrr','ppp'])
            y = self.config.getlist('childtickets', 'parent.%s.inherit' % t, default=['ddd','cweeeowner'])
            self.env.log.debug("XXXXX %s --- %s ---" % (x,y))

        # Detail view?
        if parenttype:
            if req.method == 'POST':
                changed = False

                allow_child_tickets = req.args.get('allow_child_tickets')
                self.config.set('childtickets','parent.%s.allow_child_tickets' % parenttype, allow_child_tickets)

                # NOTE: 'req.arg.get()' returns a string if only one of the multiple options is selected.
                headers = req.args.get('headers') or []
                if not isinstance(headers, list):
                    headers = [headers]
                self.config.set('childtickets','parent.%s.table_headers' % parenttype, ','.join(headers))

                restricted = req.args.get('restricted') or []
                if not isinstance(restricted, list):
                    restricted = [restricted]
                self.config.set('childtickets','parent.%s.restrict_child_type' % parenttype, ','.join(restricted))

                inherited = req.args.get('inherited') or []
                if not isinstance(inherited, list):
                    inherited = [inherited]
                self.config.set('childtickets','parent.%s.inherit' % parenttype, ','.join(inherited))

                changed = True


                if changed:
                    _save_config(self.config, req, self.log),
                req.redirect(req.href.admin(cat, page))

            # Convert to object.
            parenttype = ParentType(self.config, parenttype)

            data =  {
                    'view': 'detail',
                    'parenttype': parenttype,
                    'table_headers': self._headers(parenttype),
                    'parent_types': self._types(parenttype),
                    'inherited_fields': self._inherited(parenttype),
                    }
        else:
            data =  {
                    'view': 'list',
                    'ticket_types': [ ParentType(self.config, p) for p in self._types() ],
                    }

        # Add our own styles for the ticket lists.
        add_stylesheet(req, 'ct/css/childtickets.css')

        return 'admin_childtickets.html', data


    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ct', resource_filename(__name__, 'htdocs'))]

    # Custom methods
    def _headers(self,ptype):
        """Returns a list of valid headers for the given parent type.
        """
        HEADERS = dict.fromkeys(self.__class__.HEADERS, None)
        HEADERS.update( dict.fromkeys( map(lambda x:x.lower(),ptype.table_headers), 'checked' ))
        return HEADERS

    def _inherited(self,ptype):
        """Returns a list of inherited fields.
        """
        INHERITED = dict.fromkeys(self.__class__.INHERITED, None)
        INHERITED.update( dict.fromkeys( map(lambda x:x.lower(),ptype.inherited_fields), 'checked' ))
        return INHERITED

    def _types(self,ptype=None):
        """
        Get list of valid ticket type to work with, or of a parenttype is given, return a dictionary
        with info as to whether the parent type is already selected as an avaible child type.
        """
        # For trac 0.13 : self.env.db_query('SELECT name FROM enum WHERE type="ticket_type"')
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('select name from enum where type="ticket_type"')
        if not ptype:
            # No parent type supplied, return simple list.
            return [ x for (x,) in cursor.fetchall() ]
        else:
            # With parent type, return a dictionary.
            TYPES=dict.fromkeys([ x for (x,) in cursor.fetchall()], None)
            TYPES.update( dict.fromkeys( map(lambda x:x.lower(),ptype.restrict_to_child_types), 'checked' ))
            return TYPES


class ParentType(object):

    def __init__(self, config, name):
        self.name = name
        self.config = config

    @property
    def allow_child_tickets(self):
        return self.config.getbool('childtickets','parent.%s.allow_child_tickets' % self.name, default=False)

    @property
    def table_headers(self):
        return self.config.getlist('childtickets', 'parent.%s.table_headers' % self.name, default=['summary','owner'])

    @property
    def restrict_to_child_types(self):
        return self.config.getlist('childtickets', 'parent.%s.restrict_child_type' % self.name, default=[])

    @property
    def inherited_fields(self):
        return self.config.getlist('childtickets','parent.%s.inherit' % self.name, default=[])

    @property
    def default_child_type(self):
        return self.config.get('childtickets', 'parent.%s.default_child_type' % self.name, default=self.config.get('ticket','default_type'))

    @property
    def table_row_class(self):
        """Return a class (enabled/disabled) for the table row - allows it to 'look' disabled if not active!"""
        if self.allow_child_tickets:
            return 'enabled'
        return 'disabled'

