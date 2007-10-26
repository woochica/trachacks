# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from tracrpc.api import IXMLRPCHandler
from tracteamroster.api import UserProfilesSystem, UserProfile


class TeamRosterRPC(Component):
    """Interface to project's team roster"""
    
    implements(IXMLRPCHandler)
    
    
    # IXMLRPCHandler methods
    def xmlrpc_namespace(self):
        return 'teamroster'

    def xmlrpc_methods(self):
        yield ('WIKI_VIEW', ((list,),(int, list)), self.getTeamRoster)

    def getTeamRoster(self, req, listUserProfilesTemplate=[]):
        """Returns project's team roster.
        
        Usage:
            {{{ teamroster.getTeamRoster() # without arguments returns current active user profiles (with enabled='1') }}}
            {{{ teamroster.getTeamRoster([{role='developer', enabled='1'}]) # Returns all userProfiles with role='developer' and enabled='1' }}}
            {{{ teamroster.getTeamRoster([{name='%someName%'}]) # Returns all userProfiles with name like 'someName' }}}
        """
        if isinstance(listUserProfilesTemplate, list) and len(listUserProfilesTemplate)>0:    
            userProfileTemplates = []
            for listItem in listUserProfilesTemplate:
                if isinstance(listItem, dict):
                    userProfileTemplates.append(UserProfile(**listItem))
            
            userProfiles = UserProfilesSystem(self.env).search_userProfile(userProfileTemplates)
            return [dict(listItem) for listItem in userProfiles]
        else:
            return [dict(listItem) for listItem in UserProfilesSystem(self.env).get_active_userProfiles()]
        