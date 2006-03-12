#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2004 Edgewall Software
# Copyright (C) 2003-2004 Jonas Borgström <jonas@edgewall.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Jonas Borgström <jonas@edgewall.com>

try:
    from trac.web import cgi_frontend
    cgi_frontend.run()

except Exception, e:
    import sys
    import traceback

    print>>sys.stderr, e
    traceback.print_exc(file=sys.stderr)

    print 'Status: 500 Internal Server Error'
    print 'Content-Type: text/plain;charset=utf-8\r\n\r\n',
    print
    print 'Aïe...'
    print
    print 'Trac a détecté une erreur interne:', e
    print
    traceback.print_exc(file=sys.stdout)
