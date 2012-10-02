#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Noah Kantrowitz <noah@coderanger.net>
# Copyright (C) 2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re
import sys
import trac

def assert_trac_version(condition, name):
    # Check for allowed Trac version
    try:
        condition_re = re.match(r'^([<>=]+)\s*([0-9.]+)$', condition)
        operator = condition_re.group(1)
        version = condition_re.group(2)
        if operator in ('<', '<='):
            if not eval('trac.__version__ %s "%s"' % (operator, version)):
                print """ERROR: %s is only needed for Trac %s. Activate by setting
tracopt.ticket.deleter = enabled in Trac %s and later.""" % (name, condition, version)
                sys.exit(1)
        else:
            print "Unsupported or unrecognized operator '%s'" % operator
            sys.exit(1)
    except ImportError:
        print "ERROR: Trac not found. Install Trac before installing %s." % (name,)
        sys.exit(1)
