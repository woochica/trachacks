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

from trac.core import *

class DefaultCC(object):
    """Class representing components' default CC lists
    """

    def __init__(self, env, name, db=None):
        self.env = env
        if name:
            name = simplify_whitespace(name)
        if name:
            if not db:
                db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT cc FROM component_default_cc "
                           "WHERE name=%s", (name,))
            row = cursor.fetchone()
            if not row:
                self.name = name
                self.cc = None
            else:
                self.name = name
                self.cc = row[0] or None
        else:
            self.name = None
            self.cc = None

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
        self.name = simplify_whitespace(self.name)
        assert self.name, 'Cannot create default CC for a component with no name'
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        self.env.log.debug("Creating %s's default CC" % self.name)
        cursor.execute("INSERT INTO component_default_cc (name,cc) "
                       "VALUES (%s,%s)",
                       (self.name, self.cc))

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

def simplify_whitespace(name):
    """Strip spaces and remove duplicate spaces within names"""
    return ' '.join(name.split())
