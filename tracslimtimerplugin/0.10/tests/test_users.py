
import sys
sys.path = ['..'] + sys.path

import tracslimtimer.users as users
import unittest
import testconfig
import os

class UsersTest(unittest.TestCase):
    
    def setUp(self):
        if not self.__dict__.has_key('users'):
            self.setUpUsers()

    def setUpUsers(self):
        config_file = testconfig.get('users', 'config_file')
        if not os.path.isfile(config_file):
            self.fail("User configuration file %s is not available"
                    % config_file)

        self.users = users.Users(config_file)

    def test_existing_user(self):
        test_user = self.users.get_st_user("tracuser")
        self.assertEqual(test_user['st_user'], 'tracuser@mail.com')
        self.assertEqual(test_user['st_pass'], 'st_password')
        self.assertEqual(test_user['default_cc'], True)
        self.assertEqual(test_user['report'], False)

    def test_new_user(self):
        self.assertEqual(len(self.users.users), 1)
        new_user = self.users.add_user("")
        new_user['st_user'] = 'mystery@gmail.com'
        new_user['st_pass'] = 'mystery'
        new_user['default_cc'] = True
        new_user['report'] = True
        self.assertEqual(len(self.users.users), 2)
        self.users.save()
        self.users = None

        self.setUpUsers()
        self.assertEqual(len(self.users.users), 2)
        self.users.delete_user("__user0__")
        self.assertEqual(len(self.users.users), 1)
        self.users.save()

    def test_get_ccs(self):
        emails = self.users.get_cc_emails()
        self.assertEqual(len(emails), 1)

    def test_get_trac_from_st(self):
        test_user = self.users.get_trac_user("tracuser@mail.com")
        self.assertEqual(test_user, "tracuser")

        noone = self.users.get_trac_user("definitely@doesnt.exist")
        self.assertEqual(noone, "")

if __name__ == '__main__':
    unittest.main()

