#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from genshi.filters.transform import Transformer
from sys import maxint
from trac.config import ListOption
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
import datetime
import sys


class DecayedWiki(Component):
    """ Indicate how old the wiki page is. colors can set in [wiki]-decayed_colors in trac.ini """
    implements(ITemplateStreamFilter)

    default_colors = {
          86400 * 1: '#ffffff',
          86400 * 7: '#eeeeee',
          86400 * 31: '#dddddd',
          86400 * 365: '#aaaaaa',
          maxint: '#777777'}
    colors = ListOption('wiki', 'decay_colors',
        "86400:#ffffff, 604800:#eeeeee, 2678400:#dddddd, 31536000:#aaaaaa, 2147483647: #777777",
        doc="""
            List of (age_in_seconds: color) value pairs
            e.g. "86400:#ffffff, 604800:#cccccc, 2147483647: !#777777";

            means that the page modified in a day shows on white,
            in a week shows on light grey, and so on.
            (Provided by !ContextChrome.!DecayedWiki) """)

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if data and 'context' in data and \
                data['context'].resource.realm == 'wiki' and \
                'page' in data and data['page'].time:
            page = data['page']
            delta = (datetime.datetime.now(page.time and page.time.tzinfo or None) - page.time).total_seconds()
            try:
                colors = [color.split(':') for color in self.config.getlist('wiki', 'decay_colors')]
                colors = map(lambda kv: (int(kv[0]), kv[1]), colors)
            except:
                errorinfo = sys.exc_info()
                self.log.warning('Parse Error - using defaults, at trac.ini [wiki]/decay_colors;  %s', errorinfo)
                colors = self.default_colors.items()  # fall back
            color = 'white'  # sentinel; avoid undefined error with empty list
            for value, color in sorted(colors):
                if value > delta:
                    break
            self.log.debug('wiki decay: {wiki:%s, delta:%s, color:%s}' % (page.name, delta, color))
            return stream | Transformer('//body').attr('style', 'background-color: %s' % color)
        return stream
