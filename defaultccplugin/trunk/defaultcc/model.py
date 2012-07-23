# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 ERCIM
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Authors: Jean-Guilhem Rouel <jean-guilhem.rouel@ercim.org>
#          Vivien Lacourba <vivien.lacourba@ercim.org>
#

import re

class DefaultCC(object):
    """Class representing components' default CC lists
    """

    def __init__(self, env, name=None, db=None):
        self.env = env
        self.name = self.cc = None
        if name:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT cc FROM component_default_cc "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if row:
                self.name = name
                self.cc = row[0] or None

    def delete(self, db=None):
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.info('Deleting component %s\'s default CC' % self.name)
        cursor.execute("DELETE FROM component_default_cc WHERE name=%s", (self.name,))

        if handle_ta:
            db.commit()

    def insert(self, db=None):
        assert self.name, "Cannot create default CC for a component with no name"
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.debug("Creating %s's default CC" % self.name)
        cursor.execute("INSERT INTO component_default_cc (name,cc) "
                       "VALUES (%s,%s)",
                       (self.name, _fixup_cc_list(self.cc)))

        if handle_ta:
            db.commit()

    @classmethod
    def select(cls, env, db=None):
        if not db:
            db = env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT name,cc FROM component_default_cc "
                       "ORDER BY name")
        res = {}
        for name, cc in cursor:
            res[name] = cc

        return res

def _fixup_cc_list(cc_value):
    """Fix up cc list separators and remove duplicates."""
    cclist = []
    for cc in re.split(r'[;,\s]+', cc_value):
        if cc and cc not in cclist:
            cclist.append(cc)
    return ', '.join(cclist)
