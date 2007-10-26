# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#

from trac.core import *
from trac.config import *
from trac.perm import IPermissionRequestor

from StringIO import StringIO
import traceback

__all__=['UserProfile', 'UserProfilesSystem', 'IUserProfilesStore']

class UserProfile(dict):
    
    # reference to userProfile's store
    store = None
    exists = False
    id=-1
    
    def __init__(self, id=-1, store=None, **args):
        self.id = id
        
        self.exists = False
        self.store = store
        
        if len(args)>0:
            dict.__init__(self, **args)
        else:
            self.enabled=0
            self.name=""
            self.email=""
            self.bio=""
            self.picture_href=""
            self.role=""
            self.uniq_id=""
            
    def __getattribute__(self, name):
        """Returns userProfile's attributes.
        
        @param name: str
        """
        try:
            return object.__getattribute__(self, name)
        except AttributeError, e:
            return self.get(name)        
        
    def __setattr__(self, name, value):
        """Sets userProfile's attributes. if 'name' is an 
        userProfile's attribute, then it's added to dict.
        
        @param name: str
        @param value: 
        """
        try:
            object.__getattribute__(self, name)
            object.__setattr__(self, name, value)
            
            if name=="store":
                if isinstance(value, Component):
                    self["uniq_id"]=('%s/%s')%(value.__class__.__name__, self.id)
        except AttributeError, e:
            self[name]=value
            
    def save(self):
        """Shortcut to userProfile's 
        store
        """
        if self.store and isinstance(self.store, Component):
            return self.store.save_userProfile(self)

        
class IUserProfilesStore(Interface):
    def get_userProfile(self, userProfile_id):
        """Retuns userProfile
        
        @param userProfile_id: str
        @return: tracteamroster.api.UserProfile
        """
    def add_userProfile(self, userProfile):
        """Adds userProfile to store
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
    def save_userProfile(self, userProfile):    
        """Save/update userProfile
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
    def remove_userProfile(self, userProfile):
        """ Removes provide from store
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
    def search_userProfile(self, userProfileTemplate=None):
        """ Returns all userProfiles matching 
        userProfileTemplate
        
        @note: if userProfileTemplate it's none, then 
        all userProfiles should be returned
        
        @param userProfileTemplate: tracteamroster.api.UserProfile
        @return: list 
        """

class UserProfilesSystem(Component):
    """This component manages project's userProfiles"""
    
    implements(IPermissionRequestor)
    store = ExtensionOption('team_roster', 'user_profiles_store', IUserProfilesStore,
                            'DefaultUserProfilesStore',
        """Name of the component implementing `IUserProfilesStore`, which is used
        for storing project's team""")
    
    userProfiles_providers = OrderedExtensionsOption(section='team_roster', name='user_profiles_providers',interface=IUserProfilesStore,
                                                     default=None, include_missing=False, doc=
        """List of components that are implementing 'IUserProfilesStore'. 
        UserProfiles provided by this components can be added to local UserProfilesStore.""" )
    
    #ExtensionPoint(IUserProfilesStore)
        
    # Public API
    def get_userProfile(self, userProfile_id):
        """Returns  userProfile"""
        return self.store.get_userProfile(userProfile_id)
    
    def add_userProfile(self, userProfile):
        """Adds profile to local userProfiles store"""
        return self.store.add_userProfile(userProfile)
         
    def remove_userProfile(self, userProfile):
        """Removes profile from local userProfiles store"""
        return self.store.remove_userProfile(userProfile)
        
    def save_userProfile(self, userProfile):
        """Saves profile in local userProfiles store"""
        return self.store.save_userProfile(userProfile)
        
    def search_userProfile(self, userProfileTemplates):
        """Returns a list of userProfiles matching 
        userProfileTemplate"""
        _return = []
        _userProfileTemplates=[]
        
        if not isinstance(userProfileTemplates, list):
            _userProfileTemplates=[userProfileTemplates]
        else:
            _userProfileTemplates = userProfileTemplates
        
        for _userProfileTemplate in _userProfileTemplates: 
            for _userProfileProvider in self._get_userProfiles_providers(_userProfileTemplate.store):
                try:
                    if _userProfileTemplate.id>0:
                        _returnedUserProfile = _userProfileProvider.get_userProfile(_userProfileTemplate.id)
                        if _returnedUserProfile.id>0:
                            _return.append(_returnedUserProfile)
                    else:
                        _return.extend(_userProfileProvider.search_userProfile(_userProfileTemplate))
                except Exception, e:
                    out = StringIO()
                    traceback.print_exc(file=out)
                    self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
        return _return
        
    def get_active_userProfiles(self):
        """This method should return active team"""
        return self.store.search_userProfile(UserProfile(enabled=1))

    def _get_userProfiles_providers(self, userProfilesStore=None):
        """Returns registered userProfiles 
        providers """
        _stores = [self.store]+self.userProfiles_providers
        
        if userProfilesStore:
            if isinstance(userProfilesStore, str):
                for _userProfilesProvider in _stores:
                    if _userProfilesProvider.__class__.__name__==userProfilesStore:
                        return [_userProfilesProvider]
            # FIX ME: let's hope that userProfilesStore argument 
            # implements IUserProfilesStore
            if isinstance(userProfilesStore, Component):
                return [userProfilesStore]
            raise TracError("BAD userProfilesStore")
            
        return _stores
    
    # IPermissionRequestor methods
    def get_permission_actions(self):
        actions = ['TEAM_ADD', 'TEAM_REMOVE', 'TEAM_VIEW', 'PROFILE_MODIFY']
        return actions + [('TEAM_ADMIN', actions)]