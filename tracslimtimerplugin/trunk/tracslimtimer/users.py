
import os
import re
import elementtree.ElementTree as ET

#
# This is just a very thin wrapper around a dictionary that stores all the
# users. In the future it deserves further encapsulation with classes like
# "User" but for now it's just "the simplest thing that could possibly work."
#

class Users:
    """
    User management to match trac users with SlimTimer logins
    """

    def __init__(self, config_file):
        self.users = {}
        self._load_config(config_file)
        self.__config_file = config_file

    def save(self):
        users = ET.Element("users")

        for username, user in self.users.items():

            xml_user = ET.SubElement(users, "user")
            if not self._is_generated_username(username):
                xml_user.set("tracUser", username)

            if user.has_key('st_user') or user.has_key('st_pass'):
                st = ET.SubElement(xml_user, "slimtimer")
                st_user = ET.SubElement(st, "username")
                st_user.text = user.get('st_user','')
                st_pass = ET.SubElement(st, "password")
                st_pass.text = user.get('st_pass','')

            xml_user.set("defaultCC", 
                         ('false','true')[bool(user.get('default_cc',False))])
            xml_user.set("report",
                         ('false','true')[bool(user.get('report',False))])

        config = open(self.__config_file, 'w')
        ET.ElementTree(users).write(config)
        config.close()

    def get_st_user(self, trac_username):
        return self.users.get(trac_username)

    def get_trac_user(self, st_username):
        for username, user in self.users.items():
            if user.get('st_user', '') == st_username:
                return username

        return ''

    def get_all_users(self):
        return self.users

    def get_cc_emails(self):
        emails = []
        for user in self.users.values():
            if user.get('default_cc',False) and user.get('st_user',''):
               emails.append(user['st_user']) 
        return emails

    def get_reporter_emails(self):
        emails = []
        for user in self.users.values():
            if user.get('report',False) and user.get('st_user',''):
               emails.append(user['st_user']) 
        return emails

    def add_user(self, trac_username):
        if self.users.has_key(trac_username):
            return self.users[trac_username]

        if not trac_username:
            trac_username = self._generate_username()

        self.users[trac_username] = {}
        return self.users[trac_username]

    def delete_user(self, trac_username):
        if not self.users.has_key(trac_username):
            return

        del self.users[trac_username]

    # Internal methods

    def _load_config(self, config_file):
        if not os.path.exists(config_file):
            return

        users = ET.parse(config_file)
        if not users:
            return

        for user in users.findall("user"):
            trac_user = user.get("tracUser", "")
            if not trac_user:
                trac_user = self._generate_username()
            st_user = user.findtext("slimtimer/username")
            st_pass = user.findtext("slimtimer/password")
            default_cc = user.get("defaultCC", "false")
            report = user.get("report", "false")

            data = {}
            if (st_user): data['st_user'] = st_user
            if (st_pass): data['st_pass'] = st_pass
            data['default_cc'] = bool(default_cc in ('true','yes','1'))
            data['report'] = bool(report in ('true','yes','1'))

            self.users[trac_user] = data

    def _generate_username(self):
        for x in range(0,9999):
            name = "__user%s__" % x
            if not self.users.has_key(name):
                return name
        else:
            raise Exception("Ran out of auto-generated usernames")

    def _is_generated_username(self, username):
        return re.match("__user\d+__", username)

