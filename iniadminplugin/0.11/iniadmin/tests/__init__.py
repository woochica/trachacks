# -*- coding: utf-8 -*-

import unittest

from iniadmin.tests import iniadmin_


def suite():
    suite = unittest.TestSuite()
    suite.addTest(iniadmin_.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
