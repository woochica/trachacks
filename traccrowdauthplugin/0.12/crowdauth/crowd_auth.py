# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         crowd_auth.py
# Purpose:      The TracCrowdAuthPlugin Trac plugin handler module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

# python modules
import sys,os
import urllib
import urllib2
import urlparse

try:
    import json
except ImportError:
    import simplejson as json

# trac modules
from trac.core import *
from trac.config import Option

# trac interfaces for components
from acct_mgr.api import IPasswordStore

# third party modules
from pkg_resources import resource_filename

__all__ = ['CrowdAuthStore']

class CrowdAuthStore(Component):

    crowd_rest_base_url = Option('crowdauth', 'crowd_rest_base_url', doc='Server to use for Crowd authentication')
    crowd_realm = Option('crowdauth', 'crowd_realm', doc='Application realm for Crowd')
    crowd_useranme = Option('crowdauth', 'crowd_useranme', doc='Application user for Crowd')
    crowd_password = Option('crowdauth', 'crowd_password', doc='Application password for Crowd')
    crowd_group = Option('crowdauth', 'crowd_group', doc='Trac user group in Crowd')

    implements(
                IPasswordStore,
            )

    def __init__(self):
        pass

    # IPasswordStore methods

    def check_password(self, user, password):
        self.log.debug('CrowdAuth: Checking password for user %s', user)

        # query content
        query_content = {}
        query_content["value"] = password

        # build url
        query_data = {}
        query_data["username"] = user

        method_uri = "authentication"

        try:
            #{u'active': True,
            # u'display-name': u'User Name',
            # u'email': u'user1@example.com',
            # u'expand': u'attributes',
            # u'first-name': u'user',
            # u'last-name': u'name',
            # u'name': u'user1',
            #}
            result = self._query_crowd(method_uri, query_content, query_data)
            return True
        except Exception, e:
            self.log.error("", exc_info=True)
            return False

    def get_users(self):
        # query content
        query_content = {}

        # build url
        query_data = {}
        query_data["groupname"] = self.crowd_group

        method_uri = "group/user/nested"

        users = []
        try:
            #{u'expand': u'user',
            # u'users': [{u'name': u'liaojie'}]
            #}
            result = self._query_crowd(method_uri, query_content, query_data)
            for user in result["users"]:
                users.append(user["name"])
        except Exception, e:
            self.log.error("", exc_info=True)
        return users

    def has_user(self, user):
        return user in self.get_users()

    # internal methods
    def _query_crowd(self, method_uri, query_content, query_data):
        # build url
        query = urllib.urlencode(query_data)
        method_url = urlparse.urljoin(self.crowd_rest_base_url, method_uri)
        crowd_url = "%s?%s" % (method_url, query)

        # build request
        request = urllib2.Request(crowd_url)
        request.add_header('Accept', "application/json")
        if query_content:
            # query content
            content = json.dumps(query_content)

            # http POST
            request.add_header('Content-Type', "application/json")
            request.add_header('Content-Length', len(content))
            request.add_data(content)

        # auth
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(realm=self.crowd_realm,
                                  uri=self.crowd_rest_base_url,
                                  user=self.crowd_useranme,
                                  passwd=self.crowd_password)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)

        # query
        http_response = urllib2.urlopen(request).read()

        return json.loads(http_response)

