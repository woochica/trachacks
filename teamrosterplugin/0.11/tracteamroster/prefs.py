# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from trac.prefs.api import IPreferencePanelProvider
from trac.util.translation import _
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider

from tracteamroster.api import UserProfilesSystem
from tracteamroster.admin import TeamAdminPage


class UserProfileModule(Component):
    implements(IPreferencePanelProvider)
    
    # IPreferencePanelProvider methods
    def get_preference_panels(self, req):
        yield ('userprofile', _('My Profile'))    
        
    def render_preference_panel(self, req, panel):
        """"""
        userProfileData={}
        userProfile = UserProfilesSystem(self.env).get_userProfile(req.session.sid)
        
        if req.method=='POST' :
            userProfile.name = req.args.get('tr_userProfile_name')
            userProfile.email = req.args.get('tr_userProfile_email')
            userProfile.bio = req.args.get('tr_userProfile_bio')
            userProfile.picture_href = TeamAdminPage(self.env)._do_uploadPicture(req, userProfile, {},'tr_userProfile_picture')
            userProfile.role = req.args.get('tr_userProfile_role')
            if userProfile.save():
                userProfileData['message']='Profile updated'
        
        userProfileData['userProfile']=userProfile
        add_stylesheet(req, 'tracteamroster/css/teamroster.css')    
        
        # wiki toolbar
        add_script(req, 'common/js/wikitoolbar.js')
        add_stylesheet(req, 'common/css/wiki.css')
                
        return 'prefs_teamroster_user.html', {'teamRoster':userProfileData}
    
    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracteamroster', 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracteamroster', resource_filename(__name__, 'htdocs'))]