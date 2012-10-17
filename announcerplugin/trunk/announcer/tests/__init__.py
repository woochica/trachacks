# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(ticket_compat.suite())
    suite.addTest(ticket_formatter.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest="suite")
