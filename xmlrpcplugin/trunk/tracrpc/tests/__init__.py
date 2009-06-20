# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest
import os
import time
import urllib2

try:
    from trac.tests.functional.svntestenv import SvnFunctionalTestEnvironment

    if not hasattr(SvnFunctionalTestEnvironment, 'init'):
        raise Exception("\nTrac version is out of date. " \
            "Tests require minimum Trac 0.11.x rXXXX to run.")

    class RpcTestEnvironment(SvnFunctionalTestEnvironment):

        def __del__(self):
            print "\nStopping web server...\n"
            self.stop()
            if hasattr(SvnFunctionalTestEnvironment, '__del__'):
                SvnFunctionalTestEnvironment.__del__(self)

        def init(self):
            self.trac_src = os.path.realpath(os.path.join( 
                    __import__('trac', []).__file__, '..' , '..'))
            print "\nFound Trac source: %s" % self.trac_src
            SvnFunctionalTestEnvironment.init(self)

        def post_create(self, env):
            print "Enabling RPC plugin and permissions..."
            env.config.set('components', 'tracrpc.*', 'enabled')
            env.config.save()
            self._tracadmin('permission', 'add', 'anonymous', 'XML_RPC')
            print "Created test environment: %s" % self.dirname
            parts = urllib2.urlparse.urlsplit(self.url)
            self.url_anon = '%s://%s:%s/xmlrpc' % (parts[0], parts[1],
                                self.port)
            self.url_user = '%s://user:user@%s:%s/login/xmlrpc' % \
                                (parts[0], parts[1], self.port)
            self.url_admin = '%s://admin:admin@%s:%s/login/xmlrpc' % \
                                (parts[0], parts[1], self.port)
            self.url_anon_json = '%s://%s:%s/jsonrpc' % (parts[0], parts[1],
                                self.port)
            self.url_auth_json = '%s://%s:%s/login/jsonrpc' % (parts[0],
                                parts[1], self.port)
            print "Starting web server: %s:%s\n" % (self.url, self.port)
            self.restart()
            SvnFunctionalTestEnvironment.post_create(self, env)

        def restart(self):
            SvnFunctionalTestEnvironment.restart(self)
            # Add a delay to make sure server comes up...
            time.sleep(1)

    rpc_testenv = RpcTestEnvironment(os.path.realpath(os.path.join(
                os.path.realpath(__file__), '..', '..', '..', 'rpctestenv')),
                '8765', 'http://127.0.0.1')

    def suite():
        suite = unittest.TestSuite()
        import tracrpc.tests.json
        suite.addTest(tracrpc.tests.json.suite())
        import tracrpc.tests.ticket
        suite.addTest(tracrpc.tests.ticket.suite())
        return suite

except Exception, e:
    print e
    print "Trac test infrastructure not available."
    print "Install Trac as 'python setup.py develop' (run Trac from source).\n"
    suite = unittest.TestSuite() # return empty suite
