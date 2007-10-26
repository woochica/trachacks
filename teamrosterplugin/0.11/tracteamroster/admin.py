# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from StringIO import StringIO
import os

from trac.admin.api import IAdminPanelProvider
from trac.attachment import Attachment
from trac.core import *
from trac.config import Option
from trac.web.main import IRequestHandler, IRequestFilter
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_script
from trac.util import get_reporter_id
from trac.util.html import html
from trac.util.translation import _
from trac.wiki.formatter import wiki_to_html
from trac.wiki import WikiPage


from tracteamroster.api import UserProfilesSystem, UserProfile


class TeamAdminPage(Component):
    implements(IAdminPanelProvider, ITemplateProvider)
    
    teamRoster_wikiPage = Option('team_roster', 'wiki_page_attachment', 'TeamRosterPluginPictures',
        """Wiki Page used by TracTeamRoster plugin to manage 
        UserProfile's picture.""")
    
    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('general', _('General'), 'teamRoster', _('Manage Team'))
        
    def render_admin_panel( self, req, cat, page, path_info):
        #req.perm.assert_permission('TRAC_ADMIN')
        userProfile_id = path_info
        teamRosterData={}
        userProfilesSystem = UserProfilesSystem(self.env)
        
        if req.args.has_key('tr_cancel'):
            req.redirect(req.href.admin(cat, page))
        
        if userProfile_id:
            userProfile = userProfilesSystem.get_userProfile(userProfile_id)
            if userProfile.exists:
                if self._do_updateUserProfile(req, userProfile, teamRosterData):
                    req.redirect(req.href.admin(cat, page))
                
                teamRosterData['userProfile']=userProfile
                add_stylesheet(req, 'tracteamroster/css/teamroster.css')    
                
                # wiki toolbar
                add_script(req, 'common/js/wikitoolbar.js')
                add_stylesheet(req, 'common/css/wiki.css')

                return 'admin_teamroster_userProfile.html', {'teamRoster':teamRosterData}
            else:
                req.redirect(req.href.admin(cat, page))
        teamRosterData['lastUpdatedProfile']= UserProfile()
        
        # manage team
        if req.method=="POST":
            if req.args.has_key("tr_userProfile_update"):
                userProfile = userProfilesSystem.get_userProfile(req.args.get('tr_userProfile_id'))
                if userProfile.exists:
                    self._do_updateUserProfile(req, userProfile, teamRosterData)
                    teamRosterData['lastUpdatedProfile']=userProfile
                
            if req.args.has_key("tr_userProfile_search"):
                self._do_searchUserProfile(req, userProfilesSystem, teamRosterData)
            
            if req.args.has_key("tr_userProfile_add"):
                self._do_addUserProfile(req, userProfilesSystem, teamRosterData)
            
            if req.args.has_key("tr_userProfile_create"):
                self._do_createUserProfile(req, userProfilesSystem, teamRosterData)
            
            if req.args.has_key("tr_userProfile_remove"):
                self._do_removeUserProfile(req, userProfilesSystem, teamRosterData)
                
        self._do_listActiveProfiles(req, userProfilesSystem, cat, page, teamRosterData)
        
        add_script(req, 'tracteamroster/js/teamroster.js')
        add_stylesheet(req, 'tracteamroster/css/teamroster.css')    
        
        # wiki toolbar
        add_script(req, 'common/js/wikitoolbar.js')
        add_stylesheet(req, 'common/css/wiki.css')
        
        return 'admin_teamroster_team.html', {'teamRoster':teamRosterData}
    
    def _do_searchUserProfile(self, req, userProfilesSystem, teamRosterData):
        """ 
        @bug: SQL Injection !
        @todo: Fix it! ... later
        """
        userProfileTemplate = UserProfile(name='%'+req.args.get('tr_search_name')+'%')
        userProfiles = userProfilesSystem.search_userProfile(userProfileTemplate)
        teamRosterData['search_result'] = userProfiles
        
    def _do_addUserProfile(self, req, userProfilesSystem, teamRosterData):
        """ """    
        uniq_ids = req.args.getlist('tr_search_result_userProfile')
        userProfilesTemplates = []
        
        if uniq_ids is None:
                return False
            
        for uniq_id in uniq_ids:
            storeClassName, userProfile_id = uniq_id.split("/")[0:2]
            userProfilesTemplates.append(UserProfile(str(userProfile_id), str(storeClassName)))
            
        for userProfile in userProfilesSystem.search_userProfile(userProfilesTemplates):
            userProfilesSystem.add_userProfile(userProfile)
        
        
    def _do_createUserProfile(self, req, userProfilesSystem, teamRosterData):
        """ """    
        newUserProfile = UserProfile(id=req.args.get('tr_newprofile_id'),
                                     name=req.args.get('tr_newprofile_name'),
                                     email=req.args.get('tr_newprofile_email'),
                                     bio=req.args.get('tr_newprofile_bio'),
                                     role=req.args.get('tr_newprofile_role')
                                     )
        userProfilesSystem.add_userProfile(newUserProfile)

    def _do_removeUserProfile(self, req, userProfilesSystem, teamRosterData):
        """ """
        uniq_ids = req.args.get('tr_userProfile_id')
        
        if uniq_ids is None:
                return False
        
        userProfile = userProfilesSystem.get_userProfile(str(uniq_ids)) 
        userProfilesSystem.remove_userProfile(userProfile)
               
    def _do_listActiveProfiles(self, req, userProfilesSystem, cat, page, teamRosterData):
        """ """
        def addHref(userProfile):
            userProfile.href=req.href.admin(cat,page,userProfile.id)
            userProfile.role = userProfile.role or "[blank]"
            userProfile.name = userProfile.name or "[blank]"
            userProfile.email = userProfile.email or "[blank]"
            userProfile.bio_html = wiki_to_html(userProfile.bio, self.env, req) or "[blank]"
            return userProfile
        
        teamRosterData['activeUserProfiles']=map(addHref, userProfilesSystem.get_active_userProfiles())
        
    def _do_updateUserProfile(self, req, userProfile, teamRosterData):
        if req.method=='POST' and req.args.has_key("tr_userProfile_update"):
            
            userProfile.name = req.args.get('tr_userProfile_name', userProfile.name)
            userProfile.email = req.args.get('tr_userProfile_email', userProfile.email)
            userProfile.bio = req.args.get('tr_userProfile_bio',userProfile.bio)
            userProfile.picture_href = self._do_uploadPicture(req, userProfile, teamRosterData)
            userProfile.role = req.args.get('tr_userProfile_role', userProfile.role)
            return userProfile.save()
        return False
    
    
    def _do_uploadPicture(self, req, userProfile, teamRosterData, req_arg_picture = 'tr_userProfile_picture' ):
        
        upload = req.args.get(req_arg_picture, None)
        if upload == None or not hasattr(upload, 'filename') or not upload.filename:
            return userProfile.picture_href
        
        if hasattr(upload.file, 'fileno'):
            size = os.fstat(upload.file.fileno())[6]
        else:
            upload.file.seek(0, 2) # seek to end of file
            size = upload.file.tell()
            upload.file.seek(0)
        if size == 0:
            raise TracError(_("Can't upload empty file"))

        filename = upload.filename
        filename = filename.replace('\\', '/').replace(':', '/')        
        filename = os.path.basename(filename)
        
        if not filename:
            raise TracError(_('No file uploaded'))
        
        page = WikiPage(self.env,  self.teamRoster_wikiPage)
        if not page.exists:
            page.text="= Team Roster Pictures ="
            page.save( 'trac', 'Page created by tracteamroster component',  req.remote_addr)
       
              
        attachment = Attachment(self.env, 'wiki', self.teamRoster_wikiPage)
        attachment.author = get_reporter_id(req, 'author')
        attachment.ipnr = req.remote_addr
        attachment.insert('_'.join([userProfile.id, filename]), upload.file, size)
        
        return req.href('/'.join(['raw-attachment', 'wiki',self.teamRoster_wikiPage,attachment.filename]))
    
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracteamroster', 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracteamroster', resource_filename(__name__, 'htdocs'))]