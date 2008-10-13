# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         model.py
# Purpose:      The TracTweakUI Trac plugin db model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

"""Model classes for objects persisted in the database."""

import time

from trac.db import Table, Column, Index

class TracTweakUIModel(object):
    """Represents a table."""

    _schema = [
        Table('tractweakui_list', key='id')[
            Column('id', auto_increment=True),
            Column('time', type='int'),
            Column('path_pattern'),
            Column('filter_name'),
            Column('tweak_script'),

        ]
    ]

    def __init__(self, env, tweak_script=None):
        """Initialize a new entry with the specified attributes.

        To actually create this build log in the database, the `insert` method
        needs to be called.
        """
        self.env = env

    def del_path_pattern(cls, env, path_pattern, db=None):
        """Remove the path_pattern from the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("DELETE FROM tractweakui_list WHERE path_pattern=%s;", (path_pattern, ))

        if handle_ta:
            db.commit()

    del_path_pattern = classmethod(del_path_pattern)

    def save_tweak_script(cls, env, path_pattern, filter_name, tweak_script, db=None):
        """Insert a new tweak_script into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()

        # remove exist rows
        cursor.execute("DELETE FROM tractweakui_list WHERE path_pattern = %s AND filter_name = %s;", (path_pattern, filter_name, ))
        
        cursor.execute("INSERT INTO tractweakui_list (path_pattern, filter_name, tweak_script) VALUES (%s, %s,  %s);",
                       (path_pattern, filter_name, tweak_script,))
        if handle_ta:
            db.commit()

    save_tweak_script = classmethod(save_tweak_script)

    def insert_path_pattern(cls, env, path_pattern, db=None):
        """Insert a new path_pattern into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("INSERT INTO tractweakui_list (path_pattern) VALUES (%s);",
                       (path_pattern, ))
        if handle_ta:
            db.commit()

    insert_path_pattern = classmethod(insert_path_pattern)

    def save_path_pattern(cls, env, path_pattern, path_pattern_orig, db=None):
        """Insert a new path_pattern into the database."""
        if not db:
            db = env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False

        cursor = db.cursor()
        cursor.execute("UPDATE tractweakui_list SET path_pattern = %s WHERE path_pattern = %s;",
                       (path_pattern, path_pattern_orig))
        if handle_ta:
            db.commit()

    save_path_pattern = classmethod(save_path_pattern)

    def get_tweak_script(cls, env, path_pattern, filter_name, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tweak_script FROM tractweakui_list WHERE path_pattern = %s AND filter_name = %s;", (path_pattern, filter_name, ))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return ""

    get_tweak_script = classmethod(get_tweak_script)

    def get_path_scripts(cls, env, path_pattern, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT tweak_script FROM tractweakui_list WHERE path_pattern = %s;", (path_pattern, ))
        rows = cursor.fetchall()
        return [row[0] for row in rows if row[0]]

    get_path_scripts = classmethod(get_path_scripts)

    def get_path_patterns(cls, env, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT DISTINCT path_pattern FROM tractweakui_list ORDER BY path_pattern;")

        return [m[0] for m in cursor.fetchall()]

    get_path_patterns = classmethod(get_path_patterns)

    def get_path_filters(cls, env, path_pattern, db=None):
        """Retrieve from the database that match
        the specified criteria.
        """
        if not db:
            db = env.get_db_cnx()

        cursor = db.cursor()

        cursor.execute("SELECT filter_name FROM tractweakui_list WHERE path_pattern = %s ORDER BY filter_name;", (path_pattern, ))

        return [m[0] for m in cursor.fetchall() if m[0]]

    get_path_filters = classmethod(get_path_filters)

schema = TracTweakUIModel._schema
schema_version = 1