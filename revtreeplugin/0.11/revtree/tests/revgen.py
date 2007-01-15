# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Emmanuel Blot <emmanuel.blot@free.fr>
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

import sys
# FIXME
sys.path.append('..')

from trac.env import open_environment
from revtree import Repository, SvgRevtree
from revtree.logenhancer import Enhancer

import logging
import logging.handlers
import re

if __name__ == '__main__':
    repospath = '' # FIXME
    urlbase = 'http://localhost:8080/trunk'

    env = open_environment('') # FIXME
    env.config.parse_if_needed()   
    repos = Repository(env, 'anonymous')
    bcre = re.compile(r'^(?P<branch>branches/[^/]+|trunk|data)'
                      r'(?:/(?P<path>.*))?$')
    revrange = (1400,1520)
    repos.build(bcre, revrange, timerange=None)
    
    svgrevtree = SvgRevtree(env, repos, urlbase)
    enhancer = Enhancer(repos, svgrevtree)
    svgrevtree.add_enhancer(enhancer)
    svgrevtree.create(mode='compact') #, revisions=revrange)
    svgrevtree.build()
    svgrevtree.render()
    import os
    pwd = os.getcwd()
    svgfile = 'revtree.svg'
    svgrevtree.save(svgfile)
