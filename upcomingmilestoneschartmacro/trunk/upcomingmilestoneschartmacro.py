#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 F@lk Brettschneider aka falkb
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
# Originally based on MilestoneQueryMacro code of Nic Ferrier.
#

from genshi.core import Markup
from trac.wiki.macros import WikiMacroBase
from trac.wiki import Formatter
from trac.util.datefmt import format_datetime, format_date, from_utimestamp, utc
from trac.util.text import to_unicode
from datetime import datetime, timedelta
from StringIO import StringIO
import babel

class UpcomingMilestonesChartMacro(WikiMacroBase):
    """Display a list of the latest upcoming milestones.

      [[UpcomingMilestonesChart(%-%,10,Next 10 Milestone Dates,yellow)]]

    The pattern is a SQL LIKE pattern.
    """

    def expand_macro(self, formatter, name, text):
        option_list = text.split(",")
        pattern, max_displayed, title, overdue_color = text.split(",")

        cursor = self.env.get_db_cnx().cursor()
        cursor.execute(
            "SELECT name, due FROM milestone WHERE name like %s AND completed = 0 ORDER BY due ASC;", [pattern]
            )
        milestone_names = [mn[0] for mn in cursor]

        cursor = self.env.get_db_cnx().cursor()
        cursor.execute(
            "SELECT due FROM milestone WHERE name like %s AND completed = 0 ORDER BY due ASC;", [pattern]
            )
        milestone_dues =  [md[0] for md in cursor]

        out = StringIO()
        wikitext = "=== %s ===\n" % title
        cur_displayed = 0
        cur_idx = 0
        for m in milestone_names:
            if not max_displayed or cur_displayed < int(max_displayed):
                if milestone_dues[cur_idx]:
                    wikitext += """ * [milestone:\"%(milestonename)s\" %(milestonename)s]""" % {
                        "milestonename": m
                        }
                    date = "(%s)" % format_date(milestone_dues[cur_idx], tzinfo=formatter.req.tz, locale=formatter.req.locale)
                    if overdue_color and datetime.now(utc) > from_utimestamp(milestone_dues[cur_idx]):
                        wikitext += ' [[span(style=background-color: ' + overdue_color + ',' + date + ')]]'
                    else:
                        wikitext += ' ' + date
                    wikitext += '\n'
                    cur_displayed += 1
            cur_idx += 1
        Formatter(self.env, formatter.context).format(wikitext, out)

        return Markup(out.getvalue())
