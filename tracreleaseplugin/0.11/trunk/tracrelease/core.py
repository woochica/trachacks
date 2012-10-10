# -*- coding: utf-8 -*-

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
import model

from pkg_resources import resource_filename

from trac.core import *
from trac.mimeview import Context
from trac.config import Option
from trac.util.html import html

from trac.log import logger_factory
from trac.util.datefmt import format_datetime, parse_date
import trac.util.datefmt as datefmt
import trac.versioncontrol.web_ui.util as vcutil

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
        return ['RELEASE_VIEW',
                'RELEASE_ADMIN',
                'RELEASE_CREATE',
                'RELEASE_INSTALLPROC_CREATE']
        
        

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'release'

    def get_navigation_items(self, req):
        if req.perm.has_permission('RELEASE_VIEW', 'RELEASE_CREATE', 'RELEASE_ADMIN'):
            yield 'mainnav', 'release', html.a('Release', href = req.href.release())



    # IRequestHandler methods
    def match_request(self, req):
        if req.path_info == "/release":
            req.args['action'] = 'list'
            return True

        if req.path_info == "/release/add":
            req.args['action'] = 'add'
            return True
        
        if req.path_info == "/release/installproc":
            req.args['action'] = 'install_proc_list'
            return True

        if req.path_info == "/release/installproc/add":
            req.args['action'] = 'install_proc_add'
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
        
        match = re.match("/release/installproc/(\d+)$", req.path_info)
        if match :
            req.args['install_proc_id'] = match.group(1)
            req.args['action'] = 'install_proc_view'
            return True
        
        match = re.match("/release/installproc/([^/]+)/(\d+)$", req.path_info)
        if match and (match.group(1) in ['add', 'edit', 'view']):
            req.args['install_proc_id'] = match.group(2)
            req.args['action'] = 'install_proc_' + match.group(1)
            return True
        
        return False

    def process_request(self, req):
        self.log.info("process_request: action: %s" % req.args.get('action'))
        
        templateData = {}
        templateData['baseURL'] = req.href.release()
        templateData['ticketURL'] = req.href.ticket()
        
        add_stylesheet(req, 'common/css/ticket.css')
        
        
        if (not 'preview' in req.args) and (not 'save' in req.args) and (req.args['action'] != 'install_proc_add'):
            if 'id' in req.args:
                templateData['release'] = data.loadRelease(self, req.args['id'])
                
            if 'install_proc_id' in req.args:
                templateData['install_proc'] = data.loadInstallProcedure(self, req.args['install_proc_id'])
                
        else:
            if 'preview' in req.args:
                templateData['preview'] = True
                
            if ('install_proc_id' in req.args) or (req.args['action'] == 'install_proc_add'):
                install_proc_id = req.args.get('install_proc_id')
                install_proc_name = req.args.get('txtProcedureName')
                install_proc_description = req.args.get('txtProcedureDescription')
                install_proc_contain_files = req.args.get('chkProcedureContainFiles')
                
                templateData['install_proc'] = model.InstallProcedures(install_proc_id,
                                                                       install_proc_name,
                                                                       install_proc_description,
                                                                       install_proc_contain_files)
            
                if 'save' in req.args:
                    id = data.saveInstallProc(self, templateData['install_proc'])
                    self.log.info("process_request: saved InstallProc: %s (%s)" % (id, templateData['install_proc']))
                    if id:
                        templateData['install_proc'] = data.loadInstallProcedure(self, id)
                        req.args['action'] = 'install_proc_view'
                        preview = False
        
        if 'action' in req.args:
            if req.args['action'] == 'view':
                self.log.debug("VIEW: %s" % str(templateData['release']))
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
                
            if req.args['action'] == 'install_proc_list':
                templateData['availableInstallProcs'] = data.findInstallProcedures(self)
                return 'install_proc_list.html', templateData, None
                
            if req.args['action'] == 'install_proc_edit':
                templateData['availableInstallProcs'] = data.findInstallProcedures(self)
                return 'install_proc_edit.html', templateData, None
                
            if req.args['action'] == 'install_proc_add':
                templateData['availableInstallProcs'] = data.findInstallProcedures(self)
                return 'install_proc_add.html', templateData, None
                
            if req.args['action'] == 'install_proc_view':
                return 'install_proc.html', templateData, None
            
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
        release = model.Release()
        release.version = req.args.get("selectReleaseVersion")
        if not release.version:
            return 'release_add_1.html', templateData, None
        
        # here a version has already been selected, assume it's name as the release name
        v = data.loadVersion(self, release.version)
        templateData['releaseName'] = v['name']
        release.planned_date = v['time']
        release.description = v['description']
        release.author        = req.authname
        release.creation_date = datefmt.to_timestamp(datefmt.to_datetime(None))

        templateData['releaseAvailableProcedures'] = data.findInstallProcedures(self)

        # Setting tickets according to the selected version"
        templateData['releaseTickets'] = ""
        release.tickets = data.getVersionTickets(self, release.version)
        for ticket in release.tickets:
            templateData['releaseTickets'] = templateData['releaseTickets'] + str(ticket.ticket_id) + ","

        templateData['release'] = release
        
        return ('release_add_2.html', templateData, None)


    def _add_step_2(self, req, templateData):        
        templateData['preview'] = False
        release = model.Release()

        release.author                     = req.authname
        release.creation_date              = datefmt.to_timestamp(datefmt.to_datetime(None))
        release.errors                     = []
        release.version                    = req.args.get("selectReleaseVersion")
        release.description                = req.args.get("txtReleaseDescription")
        release.planned_date               = req.args.get("txtReleasePlannedDate")
        release.author                     = req.authname
        templateData['releaseTickets']     = req.args.get("hiddenReleaseTickets")
        templateData['releaseName']        = req.args.get("txtReleaseName")
        
        templateData['releaseSignatures']  = req.args.get("hiddenReleaseSignatures")
        release.signatures = [model.ReleaseSignee(None, signee.strip(), None) for
                              signee in templateData['releaseSignatures'].split(",") if
                              signee.strip()]
        
        ## load selected install procedures
        procs = data.findInstallProcedures(self)
        templateData['releaseAvailableProcedures'] = procs

        release.install_procedures = []
        for proc in procs:
            proc.checked = False
            sel = req.args.get("releaseProcedure_" + str(proc.id))
            if sel:
                proc.checked = True
                self.log.debug("_add_step_2: InstallProc: %s selected" % str(proc))
                arqs = req.args.get("releaseProcedureFile_" + str(proc.id))
                if arqs:
                    arqs = [arq.strip() for arq in arqs.split(",") if arq.strip()]
                    proc.files = arqs
                else:
                    arqs = None
                    
                release.install_procedures.append(model.ReleaseInstallProcedure(None, proc, arqs))
                
                try:
                    # Find node for the requested path/rev
                    repos = self.env.get_repository(req.authname)
                    self.log.debug("Tag 1.0 existe? " + (repos.has_node("/TracReleasePlugin/tags/1.0") and "sim" or "nao"))
                    if arq:
                        for arq in arqs:
                            self.log.debug("\tArquivo: " + arq)
                            arq = self.getSourcePath(arq)
                            self.log.debug("\t\t\t" + str(arq))
                            self.log.debug("\t\t\t" + (repos.has_node(arq[0]) and "sim" or "nao"))
                except Exception, e:
                    self.log.error(e)
            
            self.log.debug("Proc")
            self.log.debug("\t\t" + str(proc))
            for ip in release.install_procedures:
                self.log.debug("\n\n\t\t\t" + str(ip))

        ## valida a data planejada
        self.log.debug("Data planejada: %s" % release.planned_date)
        try:
            plnd = parse_date(release.planned_date)
            self.log.debug(plnd)
        except Exception, e:
            self.log.error(e)
            release.errors.append(e)
                
        ## load selected tickets
        for item in templateData['releaseTickets'].split(","):
            if item.strip():
                t = data.getTicket(self, item.strip())
                release.tickets.append(model.ReleaseTicket(None, t.ticket_id,
                                                           t.summary, t.component,
                                                           t.type, t.version))

        if ('preview' in req.args) or release.errors:
            templateData['preview'] = True
            self.log.debug("_add_step_2: Preview")
            self.log.debug("\n\n\nRelease: %s\n\n\n" % release)

            templateData['release'] = release
            return ('release_add_2.html', templateData, None)
            
        elif 'submit' in req.args:
            release.planned_date = plnd
            self.log.debug("_add_step_2: Submit")
            resp = data.createRelease(self,
                                      templateData['releaseName'],
                                      release.description,
                                      release.author,
                                      release.planned_date,
                                      release.tickets,
                                      release.signatures,
                                      release.install_procedures)
            if resp:
                req.redirect(req.href.release() + '/view/' + str(resp))
            else:
                return None, None, None
            
        self.log.debug("_add_step_2: nada!")
        return ('release_add_2.html', templateData, None)



    #def getSourcePath(self, arq):
    #    if arq:
    #        parts = arq.split(":")
    #        if parts and (parts[0].startswith("source")):
    #            src = [item for item in parts[1].split('"') if item]
    #            if src:
    #                return src[0]


    def _clean(self, path):
        return path.split("\"")[0].split("]")[0].strip()
        
        
    def getSourcePath(self, arq):
        e = re.compile("(\[)?(source|export)\:(\")?(.*)(\")?(.*)(\])?")
        m = e.match(arq)
        if m:
            g = m.groups()
            colchetes = g[0]
            aspas = g[2]
            path = g[3]
            if not colchetes:
                # nao tem colchetes, entao nao tem um "apelido" para o arquivo
                path = path.split("\"")[0]
                return (path, path)
            else:
                # tem colchetes, então pode ter path + alias
                path = [item for item in path.split("\"")]
                l = len(path)
                if l == 2:
                    # aspas, path, aspas, alias
                    return (self._clean(path[0]), self._clean(path[1]))
                if l == 1:
                    # aspas, path, aspas
                    if " " in path[0]:
                        path1 = path[0].split(" ")
                        return (self._clean(path1[0]), self._clean(" ".join(path1[1:])))
                    else:                    
                        return (self._clean(path[0]), self._clean(path[0]))



##  e = re.compile("(\[)(source|export)\:(\")(.*)(\")(.*)(\])")
##  e = re.compile("(\[)?(source|export)\:(\")?(.*)(\")?(.*)(\])?")






