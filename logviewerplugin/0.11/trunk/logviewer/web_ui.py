import os
from StringIO import StringIO

from trac.core import *
#from trac.config import *
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import add_stylesheet, add_script, add_notice, add_warning, ITemplateProvider
from trac.util.html import html
#from trac.util.datefmt import format_datetime
from trac.util.translation import _

from logviewer.api import LogViewerApi

class LogViewerPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
        self.api = LogViewerApi(self.env)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('general', _('General'), 'logviewer', 'Log Viewer')
            #yield ('accounts', _('Accounts'), 'usersync', 'User Sync')
        
    def render_admin_panel( self, req, cat, page, path_info):
        # here comes the page content, handling, etc.
        try:
          logfile = self.api.get_logfile_name()
          if not logfile:
            self.env.log.debug('No log file configured.')
            self.data['err'].append('There is no log file configured for this environment.')
        except IOError:
          self.env.log.debug('Got IOError - configured log file does not exist!')
          self.data['err'].append('The configured log file does not exist.')

        self.data = {}
        self.data['err'] = []
        self.data['msg'] = []
        self.data['log'] = []
        data = {}

        # OK to process?
        if logfile and req.method=="POST":
          self._do_process(req, logfile)

        # append the messages
        data['us_message'] = self.data['msg']
        data['us_error']   = self.data['err']
        data['us_log']     = self.data['log']

        # adding stylesheets
        add_stylesheet(req, 'logviewer/css/logviewer.css')

        return 'logviewer.html', data

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('logviewer', resource_filename(__name__, 'htdocs'))] 

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver/Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]


    # Internal methods
    def _do_process(self, req, logfile):
        """Process form data received via POST
        @param req     : the request
        @param logfile : logfile name
        """
        self.env.log.debug('Processing form data')
        log = self.api.get_log(logfile, req)
        self.data['log'] = log

