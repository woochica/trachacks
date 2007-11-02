# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2006 Optaros, Inc.
# All rights reserved.
#
# @author: Catalin BALAN <cbalan@optaros.com>
#
import traceback
from StringIO import StringIO

from trac.core import *
from trac.config import *
from trac.env import open_environment

from tracteamroster.api import UserProfile, IUserProfilesStore

__all__=['SafeUserProfilesStore', 'DefaultUserProfilesStore', 'MasterEnvironmentUserProfilesStore']

class SafeUserProfilesStore(Component):
    
    implements(IUserProfilesStore)
    
    # IUserProfilesStore methods
    def get_userProfile(self, userProfile_id, grabAllFieldsFromDB=False):
        """
        @param userProfile_id: str
        @return: tracteamroster.api.UserProfile
        """
        try:
            _result = list(self._get_userProfiles([userProfile_id], grabAllFieldsFromDB))
            if len(_result)>0:
                return _result[0]
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
        
        return UserProfile(-1, self)
        
    def _get_userProfiles(self, userProfile_ids, grabAllFieldsFromDB=False):
        """This method returns the profiles defined by id 
        in userProfile_ids.
        
        How it works:
        
         1. Selecting only userProfile_ids
            userProfile_id      name    value
            jdoe                name    John Doe
            jdoe                email   JohnDoe@mail.com
            jdoe                role    Technical Arhitect
            jsmith              name    Joe Smith
            jsmith              email   JoeSmith@mail.com
            jsmith              role    Senior Developer
        
        2. marching through result set 
            
            _blankProfile=UserProfile(-1)
            for sid, name, value in thisExampleData:
                if _blankProfile.id!=sid:
                    if not firstLoop:
                        #loaded _blankProfile
                        yield _blankProfile
                    _blankProfile.id==sid
                _blankProfile[name]=value
            
        # Last item from loop (in thisExampleData it's about jsmith profile ).
        # We could avoid this by adding another loop / blank line
        yield _blankProfile
         
        @todo: Cache userProfiles
        
        @param userProfile_ids: list
        @return: list
        """
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if grabAllFieldsFromDB:
            cursor.execute("SELECT sid, name, value FROM session_attribute "
                           "WHERE sid in ('%s') ORDER BY sid"%("','".join(userProfile_ids)))
        else:
            cursor.execute("SELECT sid, name, value FROM session_attribute "
                           "WHERE sid in ('%s') and name in ('%s') ORDER BY sid"%("','".join(userProfile_ids), "','".join(UserProfile())))
        _newUserProfile=UserProfile(-1, self)
        _fieldsFromDb=[]
        for sid, name, value in cursor:
            if _newUserProfile.id!=sid:
                if _newUserProfile.id!=-1:
                    _newUserProfile.store=self
                    _newUserProfile.exists=True 
                    object.__setattr__(_newUserProfile, '_fieldsFromDb', _fieldsFromDb)
                    yield _newUserProfile
                    _newUserProfile=UserProfile(0, self)
                    _fieldsFromDb=[]
                _newUserProfile.id=sid
            _newUserProfile[name]=value
            _fieldsFromDb.append(name)
        
        # last _newUserProfile 
        if _newUserProfile.id!=-1:
            _newUserProfile.store=self
            _newUserProfile.exists=True
            object.__setattr__(_newUserProfile, '_fieldsFromDb', _fieldsFromDb)
            yield _newUserProfile

    def add_userProfile(self, userProfile):
        """This method addes a userProfile to local repository.
        Since we have userProfiles coming from "every" direction, we keep a full copy in local repositiry(no liks)
        
        @param userProfile:    tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        
        if userProfile.id<0:
            return False
        
        userProfile.enabled = "1"
        userProfile.store = self
        return self.save_userProfile(userProfile)
        
    def save_userProfile(self, userProfile):
        """         
        @note: probably we should go with delete all/insert everything
        rather than update changes/insert new fields 
        
        @param userProfile:    tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        
        # grabing the old version in order identify the changes
        _oldUserProfile = self.get_userProfile(userProfile.id, grabAllFieldsFromDB=False)
        
        # identifying actions (insert, update, delete)
        def _nestedSetActions(newKey, oldKey):
            if newKey==oldKey:
                if _oldUserProfile[newKey]<>userProfile[newKey]:
                    return ('update',(userProfile[newKey], userProfile.id, newKey))
            else:
                if newKey is None:
                    return ('delete',(userProfile.id, oldKey))
                elif not newKey in _fieldsFromDb:
                        return ('insert',(userProfile.id, newKey, userProfile[newKey]))
            return False
        
        _attrs = dict(update=[], delete=[], insert=[])
        
        _fieldsFromDb = []
        try:
            if isinstance(_oldUserProfile._fieldsFromDb, list):
                _fieldsFromDb=_oldUserProfile._fieldsFromDb
        except Exception, e:
            pass 

        for _action in map(_nestedSetActions, sorted(userProfile.keys()), sorted(_fieldsFromDb)):
            if _action:
                _attrs[_action[0]].append(_action[1])
        
        # executing actions
        db = self.env.get_db_cnx()
        cursor=db.cursor()
        
        if len(_attrs['update'])>0:
            cursor.executemany("UPDATE session_attribute SET value=%s "
                                   "WHERE sid=%s AND name=%s", _attrs['update'])
        if len(_attrs['insert'])>0:           
            cursor.executemany("INSERT INTO session_attribute "
                                   "(sid,authenticated,name,value) "
                                   "VALUES(%s,1,%s,%s)", _attrs['insert'])
        # and .. commit
        db.commit()
        
        return True
        
    def remove_userProfile(self, userProfile):
        """
        @note: We don't delete a profile, we just disable it.
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        userProfile.enabled="0"
        userProfile.store = self
        return self.save_userProfile(userProfile)
                           
    def search_userProfile(self, userProfileTemplate=None):
        """ Returns all userProfiles matching userProfileTemplate.
        
        Example: self.search_userProfile(UserProfile(name='John%', email='%'))
        
        @param userProfileTemplate:    tracteamroster.api.UserProfile
        @return: list
        """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
                              
        if userProfileTemplate is None:
            cursor.execute("SELECT sid FROM session_attribute WHERE name='enabled'")
        else:
            """@note: The following line executes a query that should look like this:
                (for UserProfileTemplate(name='John%', email='%@exemple.com')):
                    SELECT  sid, 
                            count(sid) cnt 
                    FROM session_attribute 
                    WHERE name='name' AND value like 'John%' 
                       OR name='email' AND value like '%@exemple.com' 
                    GROUP BY sid 
                    HAVING cnt=2
                    
                (for UserProfileTemplate(name='John%', email='%@exemple.com', role='Dev%')):
                    SELECT  sid, 
                            count(sid) cnt 
                    FROM session_attribute 
                    WHERE name='name' AND value like 'John%' 
                       OR name='email' AND value like '%@exemple.com' 
                       OR name='role' AND value like 'Dev%' 
                    GROUP BY sid 
                    HAVING cnt=3
            
            Keeping in mind this :
                Table('session_attribute', key=('sid', 'authenticated', 'name'))[
                    Column('sid'),
                    Column('authenticated', type='int'),
                    Column('name'),
                    Column('value')], )
            """
            cursor.execute("SELECT sid, count(sid) cnt FROM session_attribute WHERE %s GROUP BY sid HAVING cnt=%s"%
                             (" OR ".join(["name='%s' AND value like '%s'"%(k, v) for k,v in userProfileTemplate.items()]),
                            len(userProfileTemplate.items())))
    
        userProfiles_ids=[id for id, cnd in cursor]
        if len(userProfiles_ids)>0:
            return self._get_userProfiles(userProfiles_ids)
        else:
            return []


class MasterEnvironmentUserProfilesStore(Component):
    """
    @note: Let's have only one Master environment userProfile store. 
    In the future this Component should support more than one 
    'linked' Environment
    """
    masterUserProfilesStore = Option('team_roster', 'master_environment', '',
        """Master Environment that hosts 'shared' userProfiles""")
    
    implements(IUserProfilesStore)
    
    def get_userProfile(self, userProfile_id):
        _masterEnv = open_environment(self.masterUserProfilesStore)
        return UserProfilesSystem(_masterEnv).get_userProfile(userProfile_id)
        
    def add_userProfile(self, userProfile):
        raise TracError("Not Implemented")
    
    def save_userProfile(self, userProfile):    
        raise TracError("Not Implemented")
        
    def remove_userProfile(self, userProfile):
        raise TracError("Not Implemented")
    
    def search_userProfile(self, userProfileTemplate=None):
        if self.masterUserProfilesStore=='':
            return []
        
        _masterEnv = open_environment(self.masterUserProfilesStore)
        
        def _changeStore(userProfile):
            userProfile.project_name = userProfile.store.env.project_name
            userProfile.store=self
            return userProfile
        
        return map( _changeStore, UserProfilesSystem(_masterEnv).search_userProfile(userProfileTemplate) )


class DefaultUserProfilesStore(Component):
    implements(IUserProfilesStore)
    
    def get_userProfile(self, userProfile_id):
        """ Returns userProfile from store.
        
        @param userProfile_id: str
        @return: tracteamroster.api.UserProfile
        """
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT sid, name, value FROM session_attribute "
                        "WHERE sid=%s and authenticated=1 ORDER BY sid", (userProfile_id,))
        _newUserProfile=UserProfile(-1, self)

        for sid, name, value in cursor:
            _newUserProfile[name] = value
            _newUserProfile.id = sid
            _newUserProfile.exists = True
        
        _newUserProfile.store = self
        
        return _newUserProfile
        
    def add_userProfile(self, userProfile):
        """ Adds userProfile to store.
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        
        if userProfile.id<0:
            return False
        
        userProfile.enabled = "1"
        userProfile.store = self
        return self.save_userProfile(userProfile)
    
    def save_userProfile(self, userProfile):    
        """ Saves userProfile in store.
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        try:
        
            # clean up 
            cursor.execute("DELETE FROM session_attribute "
                           "WHERE sid=%s and name in (%s)"%("%s",','.join(["%s"]*len(userProfile.keys()))),
                           [userProfile.id]+userProfile.keys() )
            
            # save everything
            cursor.executemany("INSERT INTO session_attribute "
                               "(sid,authenticated,name,value) "
                                "VALUES(%s,1,%s,%s)", [(userProfile.id, k, v) for k,v in userProfile.items()])
            # and .. commit
            db.commit()
            return True
        
        except Exception, e:
            out = StringIO()
            traceback.print_exc(file=out)
            self.log.error('%s: %s\n%s' % (self.__class__.__name__, str(e), out.getvalue()))
            return False
        
    def remove_userProfile(self, userProfile):
        """ Removes userProfile from store.
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: bool
        """
        if not isinstance(userProfile, UserProfile):
            raise TracError("Class %s is not a instance of UserProfile class"%(userProfile.__class__.__name__))
        
        if userProfile.id<0:
            return False
        
        userProfile.enabled = "0"
        return self.save_userProfile(userProfile)
    
    def search_userProfile(self, userProfileTemplate=None):
        """ Returns all userProfiles matching userProfileTemplate.
        
        Example: self.search_userProfile(UserProfile(name='John%', email='%'))
        
        @param userProfile: tracteamroster.api.UserProfile
        @return: list
        """
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
                              
        if userProfileTemplate is None:
            cursor.execute("SELECT sid FROM session_attribute WHERE name='enabled'")
        else:
            cursor.execute("SELECT sid, count(sid) cnt FROM session_attribute WHERE %s GROUP BY sid HAVING cnt=%s"%
                             (" OR ".join(["name='%s' AND value like '%s'"%(k, v) for k,v in userProfileTemplate.items()]),
                            len(userProfileTemplate.items())))
            
        userProfiles_ids=[id for id, cnd in cursor]
        if len(userProfiles_ids)>0:
            return [self.get_userProfile(uid) for uid in userProfiles_ids]
        else:
            return []
        