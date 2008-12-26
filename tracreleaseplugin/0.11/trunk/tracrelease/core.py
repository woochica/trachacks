# -*- coding: utf8 -*-

#
# To start developing a new Trac Plugin I used those references (and copied some of their code, too):
#
#  http://trac.edgewall.org/wiki/TracDev
#  Trac DiscussionPlugin source code: http://trac-hacks.org/wiki/DiscussionPlugin (author: http://trac-hacks.org/wiki/Blackhex)
#  Trac TimingAndEstimation plugin source code: http://trac-hacks.org/wiki/TimingAndEstimationPlugin (author: http://trac-hacks.org/wiki/bobbysmith007)
#  Trac source code
#
# As long as I could understand their licences would permit me to do this. If someone think I infringed something, please tell me and I will correct it immediatly.
# Thank you! Trac rocks! Python rocks! OSS rocks!
#

import re
import data

from pkg_resources import resource_filename

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.util.html import html

from trac.log import logger_factory
from trac.util.datefmt import format_datetime

from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.perm import IPermissionRequestor

from trac.web.chrome import add_link, add_script, add_stylesheet, \
                            add_warning, add_ctxtnav, prevnext_nav, Chrome

import trac.wiki.formatter

class ReleaseCore(Component):
    """
        The core module implements a message board, including wiki links to
        discussions, topics and messages.
    """
    implements(INavigationContributor, IRequestHandler, IPermissionRequestor, ITemplateProvider)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['RELEASE_VIEW', 'RELEASE_ADMIN', 'RELEASE_CREATE']
        
        

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'release'

    def get_navigation_items(self, req):
        if req.perm.has_permission('RELEASE_VIEW', 'RELEASE_CREATE', 'RELEASE_ADMIN'):
            yield 'mainnav', 'release', html.a('Release', href = req.href.release())



    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info == "/release":
            return True

        if req.path_info == "/release/add":
            req.args['action'] = 'add'
            return True

        match = re.match("/release/(\d+)$", req.path_info)
        if match:
            req.args['id'] = match.group(1)
            req.args['action'] = 'view'
            return True
        
        match = re.match("/release/([^/]+)/(\d+)$", req.path_info)
        if match and (match.group(1) in ['edit', 'view', 'install', 'sign', 'signed']):
            req.args['id'] = match.group(2)
            req.args['action'] = match.group(1)
            return True
        
        return False

    def process_request(self, req):
        templateData = {}
        templateData['baseURL'] = req.href.release()
        templateData['ticketURL'] = req.href.ticket()
        
        add_stylesheet(req, 'common/css/ticket.css')
        
        if 'id' in req.args:
            templateData['release'] = data.loadRelease(self, req.args['id'])

        
        if 'action' in req.args:
            if req.args['action'] == 'view':
                return 'release_view.html', templateData, None

            if req.args['action'] == 'edit':
                templateData['availableVersions'] = data.findAvailableVersions(self)
                req.send_response(200)
                req.send_header('Content-Type', 'text/plain')
                req.end_headers()
                req.write("You can't edit an existing Release for now")
        
            if req.args['action'] == 'add':
                if req.method == "POST":
                    self.log.debug("Adding: POST")
                    ret = self._add_release(req, templateData)
                    self.log.debug(templateData)
                    self.log.debug(ret)
                    return ret[0], ret[1], ret[2]
                else:
                    self.log.debug("Adding: GET")
                    
                templateData['availableVersions'] = data.findAvailableVersions(self)
                self.log.debug(templateData)
                return 'release_add_1.html', templateData, None

            if req.args['action'] == 'install':
                return 'release_install.html', templateData, None
            
            if req.args['action'] == 'sign':
                return 'release_sign.html', templateData, None

            if req.args['action'] == 'signed':
                data.signRelease(self, req.args['id'], req.authname)
                req.redirect(req.href.release() + '/view/' + req.args['id'])
            
        # exibe listagem de releases existentes
        templateData['baseURL'] = req.href.release()
        templateData['releases'] = data.findAvailableReleases(self)
        self.log.debug(templateData['releases'])
        return 'release.html', templateData, None



    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('Release', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        genshi templates.
        """
        rtn = [resource_filename(__name__, 'templates')]
        self.log.debug(rtn)
        return rtn





    def _add_release(self, req, templateData):
        step = req.args.get("hiddenReleaseStep")
        if not step:
            step = "1"
            
        if step == "1":
            return self._add_step_1(req, templateData)
            
        elif step == "2":
            return self._add_step_2(req, templateData)



    def _add_step_1(self, req, templateData):
        templateData['releaseVersion'] = req.args.get("selectReleaseVersion")
        if not templateData['releaseVersion']:
            return 'release_add_1.html', templateData, None
        
        # here a version has already been selected, assume it's name as the release name
        v = data.loadVersion(self, templateData['releaseVersion'])
        templateData['releaseName'] = v['name']
        templateData['releasePlannedData'] = v['time']
        templateData['releaseDescription'] = v['description']
        templateData['releaseProcedureItems'] = data.findInstallProcedures(self)

        # Setting tickets according to the selected version"
        templateData['releaseTickets'] = ""
        templateData['releaseTicketItems'] = data.getVersionTickets(self, templateData['releaseVersion'])
        for ticket in templateData['releaseTicketItems']:
            templateData['releaseTickets'] = templateData['releaseTickets'] + str(ticket.ticket_id) + ","
        
        return ('release_add_2.html', templateData, None)


    def _add_step_2(self, req, templateData):
        templateData['preview']            = 'preview' in req.args
        templateData['releaseVersion']     = req.args.get("selectReleaseVersion")
        templateData['releaseName']        = req.args.get("txtReleaseName")
        templateData['releaseDescription'] = req.args.get("txtReleaseDescription")
        templateData['releasePlannedDate'] = req.args.get("txtReleasePlannedDate")
        templateData['releaseTickets']     = req.args.get("hiddenReleaseTickets")
        templateData['releaseSignatures']  = req.args.get("hiddenReleaseSignatures")
        
        if templateData['preview']:
            self.log.debug("_add_step_2: Preview")
            ## load selected tickets
            templateData['releaseTicketItems'] = []
            for item in templateData['releaseTickets'].split(","):
                templateData['releaseTicketItems'].append(data.getTicket(self, item))
                
            ## load selected install procedures
            templateData['releaseProcedureItems'] = []
            procs = data.findInstallProcedures(self)
            for proc in procs:
                sel = req.args.get("releaseProcedure_" + str(proc.id))
                if sel:
                    templateData['releaseProcedureItems'].append(proc)
            
            return ('release_add_2.html', templateData, None)
        elif 'submit' in req.args:
            self.log.debug("_add_step_2: Submit")
            resp = data.createRelease(self, templateData['releaseName'], templateData['releaseDescription'],
                                      req.authname, None, templateData['releaseTickets'],
                                      templateData['releaseSignatures'])
            if resp:
                req.redirect(req.href.release() + '/view/' + str(resp))
            else:
                return None, None, None
            
        self.log.debug("_add_step_2: nada!")
        return ('release_add_2.html', templateData, None)
