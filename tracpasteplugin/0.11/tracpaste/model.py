# -*- coding: utf-8 -*-
"""
    tracpaste.model
    ~~~~~~~~~~~~~~~
"""
from trac.core import *
from trac.wiki.api import Context
from trac.mimeview.api import Mimeview
from trac.util.datefmt import utc, to_timestamp
from datetime import datetime


def get_recent_pastes(env, n=10, db=None):
    """Return the last `n` pastes as dicts without data."""
    cursor = (db or env.get_db_cnx()).cursor()
    cursor.execute('select id, title, author, time from pastes order by '
                   'id desc limit 0, %s', (n,))
    result = []
    for row in cursor:
        result.append({
            'id':           row[0],
            'title':        row[1],
            'author':       row[2],
            'time':         datetime.fromtimestamp(row[3], utc)
        })
    return result


class Paste(object):
    """
    A class representing a paste.
    """

    def __init__(self, env, id=None, title=u'', author=u'',
                 mimetype='text/plain', data=u'', time=None):
        self.env = env
        self.id = id
        self.title = title
        self.author = author
        self.mimetype = mimetype
        self.data = data
        self.time = time

        if id is not None:
            db = env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute('select title, author, mimetype, data, time '
                           'from pastes where id = %s', (id,))
            row = cursor.fetchone()
            if row:
                self.title, self.author, self.mimetype, self.data, time = row
                self.time = datetime.fromtimestamp(time, utc)
            else:
                self.id = None

    def __repr__(self):
        return '<%s %r: %s>' % (
            self.__class__.__name__,
            self.title,
            self.id
        )

    def __nonzero__(self):
        return self.id is not None

    exists = property(__nonzero__)

    def delete(self, db=None):
        """Delete a paste"""
        if db:
            handle_ta = False
        else:
            handle_ta = True
            db = self.env.get_db_cnx()
        cursor = db.cursor()

        if self.id is None:
            raise ValueError('cannot delete not existing paste')
        cursor.execute('delete from pastes where id = %s', (self.id,))

        if handle_ta:
            db.commit()

    def save(self, db=None):
        """Save changes or add a new paste."""
        if db:
            handle_ta = False
        else:
            handle_ta = True
            db = self.env.get_db_cnx()
        cursor = db.cursor()

        if self.time is None:
            self.time = datetime.now(utc)

        if self.id is None:
            cursor.execute('insert into pastes (title, author, mimetype, '
                           'data, time) values (%s, %s, %s, %s, %s)',
                           (self.title, self.author, self.mimetype, self.data,
                            to_timestamp(self.time)))
            self.id = db.get_last_id(cursor, 'pastes')
        else:
            cursor.execute('update pastes set title=%s, author=%s, mimetype=%s,'
                           'data=%s, time=%s where id = %s', (
                self.title, self.author, self.mimetype, self.data,
                to_timestamp(self.time), self.id
            ))

        if handle_ta:
            db.commit()

    def render(self, req):
        """Render the data."""
        context = Context(self.env, req)
        mimeview = Mimeview(self.env)
        return mimeview.render(context, self.mimetype, self.data,
                               annotations=['lineno'])
