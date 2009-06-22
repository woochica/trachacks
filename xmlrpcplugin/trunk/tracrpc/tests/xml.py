# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import unittest

import xmlrpclib

from tracrpc.tests import rpc_testenv

class RpcXmlTestCase(unittest.TestCase):
    
    def setUp(self):
        self.anon = xmlrpclib.ServerProxy(rpc_testenv.url_anon)
        self.user = xmlrpclib.ServerProxy(rpc_testenv.url_user)
        self.admin = xmlrpclib.ServerProxy(rpc_testenv.url_admin)

    def test_xmlrpc_permission(self):
        # Test returned response if not XML_RPC permission
        rpc_testenv._tracadmin('permission', 'remove', 'anonymous',
                                'XML_RPC')
        try:
            self.anon.system.listMethods()
            rpc_testenv._tracadmin('permission', 'add', 'anonymous',
                                        'XML_RPC')
            self.fail("Revoked permissions not taken effect???")
        except xmlrpclib.Fault, e:
            self.assertEquals(1, e.faultCode)
            self.assertTrue('XML_RPC' in e.faultString)
            rpc_testenv._tracadmin('permission', 'add', 'anonymous',
                                        'XML_RPC')

    def test_method_not_found(self):
        try:
            self.admin.system.doesNotExist()
            self.fail("What? Method exists???")
        except xmlrpclib.Fault, e:
            self.assertEquals(1, e.faultCode)
            self.assertTrue("not found" in e.faultString)

    def test_wrong_argspec(self):
        try:
            self.admin.system.listMethods("hello")
            self.fail("Oops. Wrong argspec accepted???")
        except xmlrpclib.Fault, e:
            self.assertEquals(2, e.faultCode)
            self.assertTrue("listMethods() takes exactly 2 arguments" \
                                    in e.faultString)

    def test_content_encoding(self):
        test_string = "øæåØÆÅàéüoö"
        # No encoding / encoding error
        self.assertRaises(xmlrpclib.ProtocolError, 
                self.admin.ticket.create, test_string, test_string[::-1], {})
        # Unicode version (encodable)
        from trac.util.text import to_unicode
        test_string = to_unicode(test_string)
        t_id = self.admin.ticket.create(test_string, test_string[::-1], {})
        self.assertTrue(t_id > 0)
        result = self.admin.ticket.get(t_id)
        self.assertEquals(result[0], t_id)
        self.assertEquals(result[3]['summary'], test_string)
        self.assertEquals(result[3]['description'], test_string[::-1])
        self.assertEquals(unicode, type(result[3]['summary']))
        self.admin.ticket.delete(t_id)

def suite():
    return unittest.makeSuite(RpcXmlTestCase)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
