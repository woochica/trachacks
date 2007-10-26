# -*- coding: utf-8 -*-

import doctest
import unittest

from tracteamroster.tests import api, macros

def suite():    
    suite = unittest.TestSuite()
    suite.addTest(api.suite())
    suite.addTest(macros.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
