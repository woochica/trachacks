# -*- coding: utf-8 -*-

import os.path
import shutil
import tempfile
import unittest


from trac.test import EnvironmentStub, Mock
from tracteamroster.api import UserProfilesSystem, UserProfile
import tracteamroster.userprofiles_stores
_testUserProfiles = [
                     dict( _user='jfoo',
                           _name = 'John Foo',
                           _email= 'john.foo@testing.org',
                           _picture_href= "http://pictures.url.org/picture.jpg",
                           _bio="Blah Blah Blah Blah Blah .... and Blah",
                           _role="Junior Developer"
                           ),
                           
                     dict( _user="jfriend",
                           _name = 'John Foo Friend',
                           _email= "john.foo12@testing.org",
                           _picture_href= "http://pictures.url.btian.org/picture.jpg",
                           _bio="Blah Blah Blah Blah Blah .... and Blah",
                           _role="Senior Developer"
                           ),
                           
                     dict( _user='jguru',
                           _name = 'John Guru ',
                           _email= "john.foo@guru.org",
                           _picture_href= "http://guru.url.btian.org/picture.jpg",
                           _bio="Blah Blah Blah Blah Blah .... and Guru Blah ",
                           _role="Technical Arhitect"
                           )
                     ]

class DefaultUserProfilesStoreTestCase(unittest.TestCase):

    def setUp(self):
        self.basedir = os.path.realpath(tempfile.mkdtemp())
        self.env = EnvironmentStub(enable=['trac.*','tracteamroster.*'])
        self.env.path = os.path.join(self.basedir, 'trac-tempenv')
        os.mkdir(self.env.path)    
        self.userProfilesSystem = UserProfilesSystem(self.env)

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_add_userProfile_1(self):
        """Add new userProfile """
        
        newUserProfile = UserProfile()
        newUserProfile.id = _testUserProfiles[0].get('_user')
        newUserProfile.name = _testUserProfiles[0].get('_name')
        newUserProfile.email =_testUserProfiles[0].get('_email')
        newUserProfile.picture_href = _testUserProfiles[0].get('_picture_href')
        newUserProfile.bio = _testUserProfiles[0].get('_bio')
        newUserProfile.role = _testUserProfiles[0].get('_role')
        
        self.userProfilesSystem.add_userProfile(newUserProfile)
        
        db=self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, value FROM session_attribute WHERE sid=%s',(_testUserProfiles[0].get('_user'),))
        
        _result = {}
        for name,value in cursor:
            _result[name]=value
        
        self.assertEqual(_result['enabled'], "1")
        self.assertEqual(_result['name'], _testUserProfiles[0].get('_name'))
        self.assertEqual(_result['email'], _testUserProfiles[0].get('_email'))
        self.assertEqual(_result['picture_href'], _testUserProfiles[0].get('_picture_href'))
        self.assertEqual(_result['bio'], _testUserProfiles[0].get('_bio'))
        self.assertEqual(_result['role'], _testUserProfiles[0].get('_role'))
    
    def test_add_userProfile_2(self):
        """Add new userProfile using only the constructor"""
        
        newUserProfile = UserProfile( id=_testUserProfiles[1].get('_user'),
                                      name=_testUserProfiles[1].get('_name'),
                                      email=_testUserProfiles[1].get('_email'),
                                      picture_href=_testUserProfiles[1].get('_picture_href'),
                                      bio=_testUserProfiles[1].get('_bio'),
                                      role=_testUserProfiles[1].get('_role')
                                    )
        
        self.userProfilesSystem.add_userProfile(newUserProfile)
        
        db=self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT name, value FROM session_attribute WHERE sid=%s',(_testUserProfiles[1].get('_user'),))
        
        _result = {}
        for name,value in cursor:
            _result[name]=value
        
        self.assertEqual(_result['enabled'], "1")
        self.assertEqual(_result['name'], _testUserProfiles[1].get('_name'))
        self.assertEqual(_result['email'], _testUserProfiles[1].get('_email'))
        self.assertEqual(_result['picture_href'], _testUserProfiles[1].get('_picture_href'))
        self.assertEqual(_result['bio'], _testUserProfiles[1].get('_bio'))
        self.assertEqual(_result['role'], _testUserProfiles[1].get('_role'))
        
        
       
    def test_get_activeUserProfiles(self):
        """Get team""" 
        self._loadData()
        
        team = self.userProfilesSystem.get_active_userProfiles()
        self.assertEqual(len(list(team)),3)
    
    def test_get_userProfileById(self):
        """Get userProfile by id"""
        self._loadData()
        
        userProfile=self.userProfilesSystem.get_userProfile(_testUserProfiles[0].get('_user'))
        
        self.assertEqual(userProfile.name,_testUserProfiles[0].get('_name') )
        self.assertEqual(userProfile.email,_testUserProfiles[0].get('_email') )
        self.assertEqual(userProfile.picture_href,_testUserProfiles[0].get('_picture_href') )
        self.assertEqual(userProfile.bio,_testUserProfiles[0].get('_bio') )
        self.assertEqual(userProfile.role,_testUserProfiles[0].get('_role') )
            
    def test_get_searchUserProfilesByName(self):
        """Search userProfiles by name""" 
        
        self._loadData()
        
        searchResult = list(self.userProfilesSystem.search_userProfile(UserProfile(name="%Foo%")))
        
        self.assertEqual(len(searchResult),2)
        
        self.assertEqual(searchResult[0].name,_testUserProfiles[0].get('_name') )
        self.assertEqual(searchResult[0].email,_testUserProfiles[0].get('_email') )
        self.assertEqual(searchResult[0].picture_href,_testUserProfiles[0].get('_picture_href') )
        self.assertEqual(searchResult[0].bio,_testUserProfiles[0].get('_bio') )
        self.assertEqual(searchResult[0].role,_testUserProfiles[0].get('_role') )
        
        self.assertEqual(searchResult[1].name,_testUserProfiles[1].get('_name') )
        self.assertEqual(searchResult[1].email,_testUserProfiles[1].get('_email') )
        self.assertEqual(searchResult[1].picture_href,_testUserProfiles[1].get('_picture_href') )
        self.assertEqual(searchResult[1].bio,_testUserProfiles[1].get('_bio') )
        self.assertEqual(searchResult[1].role,_testUserProfiles[1].get('_role') )
    
    def test_get_searchUserProfiles(self):
        """Search userProfiles """ 
        
        self._loadData()
        
        searchResult = list(self.userProfilesSystem.search_userProfile(UserProfile(name="John%", role="%Dev%")))
        
        self.assertEqual(len(searchResult),2)
        
        self.assertEqual(searchResult[0].name,_testUserProfiles[0].get('_name') )
        self.assertEqual(searchResult[0].email,_testUserProfiles[0].get('_email') )
        self.assertEqual(searchResult[0].picture_href,_testUserProfiles[0].get('_picture_href') )
        self.assertEqual(searchResult[0].bio,_testUserProfiles[0].get('_bio') )
        self.assertEqual(searchResult[0].role,_testUserProfiles[0].get('_role') )
        
        self.assertEqual(searchResult[1].name,_testUserProfiles[1].get('_name') )
        self.assertEqual(searchResult[1].email,_testUserProfiles[1].get('_email') )
        self.assertEqual(searchResult[1].picture_href,_testUserProfiles[1].get('_picture_href') )
        self.assertEqual(searchResult[1].bio,_testUserProfiles[1].get('_bio') )
        self.assertEqual(searchResult[1].role,_testUserProfiles[1].get('_role') )
    
    
    def test_updateUserProfile(self):
        """Update userProfile""" 
        
        self._loadData()
    
        userProfile4=self.userProfilesSystem.get_userProfile(_testUserProfiles[1].get('_user'))
        userProfile4.email="newEmailAddress@example.org"
        userProfile4.name="Matei"
        userProfile4.enabled="0"
        userProfile4.save()
        
        userProfile_new=self.userProfilesSystem.get_userProfile(_testUserProfiles[1].get('_user'))
        self.assertEqual(userProfile_new.email, "newEmailAddress@example.org")
        self.assertEqual(userProfile_new.name, "Matei")
        self.assertEqual(userProfile4.enabled,"0")
        
    def _loadData(self):
        self.userProfilesSystem.add_userProfile(UserProfile(
                                      id=_testUserProfiles[0].get('_user'),
                                      name=_testUserProfiles[0].get('_name'),
                                      email=_testUserProfiles[0].get('_email'),
                                      picture_href=_testUserProfiles[0].get('_picture_href'),
                                      bio=_testUserProfiles[0].get('_bio'),
                                      role=_testUserProfiles[0].get('_role')
                                    )
        )
        
        
        self.userProfilesSystem.add_userProfile(UserProfile(
                                      id=_testUserProfiles[1].get('_user'),
                                      name=_testUserProfiles[1].get('_name'),
                                      email=_testUserProfiles[1].get('_email'),
                                      picture_href=_testUserProfiles[1].get('_picture_href'),
                                      bio=_testUserProfiles[1].get('_bio'),
                                      role=_testUserProfiles[1].get('_role')
                                    )
        )
        
        self.userProfilesSystem.add_userProfile(UserProfile(
                                      id=_testUserProfiles[2].get('_user'),
                                      name=_testUserProfiles[2].get('_name'),
                                      email=_testUserProfiles[2].get('_email'),
                                      picture_href=_testUserProfiles[2].get('_picture_href'),
                                      bio=_testUserProfiles[2].get('_bio'),
                                      role=_testUserProfiles[2].get('_role')
                                    )
        )
        
class SafeUserProfilesStoreTestCase(DefaultUserProfilesStoreTestCase):
    
    def setUp(self):
        DefaultUserProfilesStoreTestCase.setUp(self)
        self.env.config.set('team_roster', 'user_profiles_store', 'SafeUserProfilesStore')
              
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DefaultUserProfilesStoreTestCase, 'test'))
    suite.addTest(unittest.makeSuite(SafeUserProfilesStoreTestCase, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')