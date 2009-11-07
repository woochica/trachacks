import os
from StringIO import StringIO

from trac.core import *
from trac.config import *
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

    # Configuration options.
    _autoload = BoolOption('logviewer', 'autoload', 'false',
      doc = 'Whether the log file content should be automatically loaded when'
            ' the module is called, i.e. even before the form was submitted.'
            ' This is a boolean option (true/false), and defaults to false.')
    _autolevel = Option('logviewer', 'autolevel', '3',
      doc = 'Which log level shall be used on autoload (only applies when'
            ' autoload is enabled). This integer value defaults to 3 (warnings).'
            ' Possible values: 1=critical, 2=error, 3=warning, 4=info, 5=debug')
    _autoup = BoolOption('logviewer', 'autoup', 'true',
      doc = 'Include log events of higher levels than autolevel on autoload?'
            ' This boolean option defaults to true - and only applies on autoload')
    _autotail = Option('logviewer', 'autotail', '1000',
      doc = 'Only applies to autoload: Restrict the evaluated lines to the last N'
            ' lines. Defaults to 1000.')
    _defaultlevel = Option('logviewer', 'defaultlevel', '3',
      doc = 'Preset for the log level dropdown (if autoload is disabled). This'
            ' integer value defaults to 3 (warnings). Possible values:'
            ' 1=critical, 2=error, 3=warning, 4=info, 5=debug')
    _defaultup = BoolOption('logviewer', 'defaultup', 'true',
      doc = 'Check the box to include log events of higher levels when autoload'
            ' is disabled? This boolean option defaults to true.')
    _defaulttail = Option('logviewer', 'defaulttail', '',
      doc = 'Preset for the Tail input (restrict query to the last N lines of the'
            ' logfile to load). This must be a number (integer), and by default is'
            ' empty (not set)')

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('general', _('General'), 'logviewer', 'Log Viewer')
            #yield ('accounts', _('Accounts'), 'usersync', 'User Sync')
        
    def render_admin_panel( self, req, cat, page, path_info):
        # here comes the page content, handling, etc.
        self.data = {}
        self.data['err'] = []
        self.data['msg'] = []
        self.data['log'] = []
        data = {}
        autoload = self.env.config.getbool('logviewer','autoload') or False
        try:
          logfile = self.api.get_logfile_name()
          if not logfile:
            self.env.log.debug('No log file configured.')
            self.data['err'].append('There is no log file configured for this environment.')
        except IOError:
          self.env.log.debug('Got IOError - configured log file does not exist!')
          self.data['err'].append('The configured log file does not exist.')

        # OK to process?
        if logfile:
          params = {}
          if req.method=="POST":
            params['level'] = req.args.get('level')
            params['up']    = req.args.get('up')
            params['invert']= req.args.get('invertsearch')
            params['regexp']= req.args.get('regexp')
            params['tail']  = int(req.args.get('tail') or 0)
            params['filter']= req.args.get('filter')
            self._do_process(params, logfile)
            data['level'] = int(req.args.get('level') or 3)
            data['up']    = int(req.args.get('up') or 0)
            data['invert']= int(req.args.get('invertsearch') or 0)
            data['regexp']= int(req.args.get('regexp') or 0)
            data['filter']= req.args.get('filter') or ''
            data['tail']  = req.args.get('tail') or ''
          elif autoload:
            data['level'] = int(self.env.config.get('logviewer','autolevel') or 3)
            data['up']    = int(self.env.config.getbool('logviewer','autoup') or True)
            data['invert']= 0
            data['regexp']= 0
            data['filter']= ''
            data['tail']  = self.env.config.get('logviewer','autotail') or ''
            self._do_process(data, logfile)
          else:
            data['level'] = int(self.env.config.get('logviewer','defaultlevel') or 3)
            data['up']    = int(self.env.config.getbool('logviewer','defaultup') or True)
            data['invert']= 0
            data['regexp']= 0
            data['filter']= ''
            data['tail']  = self.env.config.get('logviewer','defaulttail') or ''

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
    def _do_process(self, params, logfile):
        """Process form data received via POST
        @param params  : config parameters
        @param logfile : logfile name
        """
        self.env.log.debug('Processing form data')
        log = self.api.get_log(logfile, params)
        self.data['log'] = log

