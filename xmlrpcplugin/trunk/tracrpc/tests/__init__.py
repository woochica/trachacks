# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009-2013 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest
import os
import time
import urllib2

from tracrpc.util import PY24

try:
    from trac.tests.functional.svntestenv import SvnFunctionalTestEnvironment

    if not hasattr(SvnFunctionalTestEnvironment, 'init'):
        raise Exception("\nTrac version is out of date. " \
            "Tests require minimum Trac 0.11.5dev r8303 to run.")

    class RpcTestEnvironment(SvnFunctionalTestEnvironment):

        def init(self):
            self.trac_src = os.path.realpath(os.path.join( 
                    __import__('trac', []).__file__, '..' , '..'))
            print "\nFound Trac source: %s" % self.trac_src
            SvnFunctionalTestEnvironment.init(self)
            self.url = "%s:%s" % (self.url, self.port)

        def post_create(self, env):
            print "Enabling RPC plugin and permissions..."
            env.config.set('components', 'tracrpc.*', 'enabled')
            env.config.save()
            self.getLogger = lambda : env.log
            self._tracadmin('permission', 'add', 'anonymous', 'XML_RPC')
            print "Created test environment: %s" % self.dirname
            parts = urllib2.urlparse.urlsplit(self.url)
            # Regular URIs
            self.url_anon = '%s://%s/rpc' % (parts[0], parts[1])
            self.url_auth = '%s://%s/login/rpc' % (parts[0], parts[1])
            # URIs with user:pass as part of URL
            self.url_user = '%s://user:user@%s/login/xmlrpc' % \
                                (parts[0], parts[1])
            self.url_admin = '%s://admin:admin@%s/login/xmlrpc' % \
                                (parts[0], parts[1])
            SvnFunctionalTestEnvironment.post_create(self, env)
            print "Starting web server: %s" % self.url
            self.restart()

        def _tracadmin(self, *args, **kwargs):
            do_wait = kwargs.pop('wait', False)
            SvnFunctionalTestEnvironment._tracadmin(self, *args, **kwargs)
            if do_wait: # Delay to ensure command executes and caches resets
                time.sleep(5)

    rpc_testenv = RpcTestEnvironment(os.path.realpath(os.path.join(
                os.path.realpath(__file__), '..', '..', '..', 'rpctestenv')),
                '8765', 'http://127.0.0.1')

    import atexit
    atexit.register(rpc_testenv.stop)

    def test_suite():
        suite = unittest.TestSuite()
        import tracrpc.tests.api
        suite.addTest(tracrpc.tests.api.test_suite())
        import tracrpc.tests.xml_rpc
        suite.addTest(tracrpc.tests.xml_rpc.test_suite())
        import tracrpc.tests.json_rpc
        suite.addTest(tracrpc.tests.json_rpc.test_suite())
        import tracrpc.tests.ticket
        suite.addTest(tracrpc.tests.ticket.test_suite())
        import tracrpc.tests.wiki
        suite.addTest(tracrpc.tests.wiki.test_suite())
        import tracrpc.tests.web_ui
        suite.addTest(tracrpc.tests.web_ui.test_suite())
        import tracrpc.tests.search
        suite.addTest(tracrpc.tests.search.test_suite())
        return suite

except Exception, e:
    import sys, traceback
    traceback.print_exc(file=sys.stdout)
    print "Trac test infrastructure not available."
    print "Install Trac as 'python setup.py develop' (run Trac from source).\n"
    test_suite = unittest.TestSuite() # return empty suite
    
    TracRpcTestCase = unittest.TestCase
else :
    __unittest = 1          # Do not show this module in tracebacks
    class TracRpcTestCase(unittest.TestCase):
        def setUp(self):
            log = rpc_testenv.get_trac_environment().log
            log.info('=' * 70)
            log.info('(TEST) Starting %s.%s',
                        self.__class__.__name__,
                        PY24 and getattr(self, '_TestCase__testMethodName') \
                            or getattr(self, '_testMethodName', ''))
            log.info('=' * 70)

        def failUnlessRaises(self, excClass, callableObj, *args, **kwargs):
            """Enhanced assertions to detect exceptions."""
            try:
                callableObj(*args, **kwargs)
            except excClass, e:
                return e
            except self.failureException :
                raise
            except Exception, e :
                if hasattr(excClass, '__name__'): excName = excClass.__name__
                else: excName = str(excClass)

                if hasattr(e, '__name__'): excMsg = e.__name__
                else: excMsg = str(e)

                raise self.failureException("\n\nExpected %s\n\nGot %s : %s" % (
                                        excName, e.__class__.__name__, excMsg))
            else:
                if hasattr(excClass,'__name__'): excName = excClass.__name__
                else: excName = str(excClass)
                raise self.failureException, "Expected %s\n\nNothing raised" % excName

        assertRaises = failUnlessRaises
