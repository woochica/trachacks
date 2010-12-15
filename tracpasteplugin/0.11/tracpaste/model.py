# -*- coding: utf-8 -*-
"""
TracPastePlugin: entity model for pastes, including:
 * CRUD (create, read, update, delete)
 * various helpers to retrieve pastes
"""

from trac.core import *
from trac.resource import Resource, ResourceNotFound
from trac.mimeview.api import Mimeview, Context
from trac.util.datefmt import utc, to_timestamp
from trac.util.translation import _
from datetime import datetime


def get_pastes(env, number=None, offset=None, from_dt=None, to_dt=None, db=None):
    """Returns a list of pastes as dicts without data.

    One or more filters need to be set:
     * number - maximum number of items that may be returned
     * offset - number of items to skip in returned results
     * from_dt - pasted on or after the given time (datetime object)
     * to_dt - pasted before or on the given time (datetime object)

    Returns dictionary of the form:
        (id, title, author, time)
    where time is in UTC.

    To get the paste data, use id to instantiate a Paste object."""

    db = db or env.get_db_cnx()
    cursor = db.cursor()

    sql = "SELECT id, title, author, time FROM pastes"
    order_clause = " ORDER BY id DESC"
    limit_clause = ""
    if number:
        limit_clause += " LIMIT %s" % number
    if offset:
        limit_clause += " OFFSET %s" % offset

    where_clause = ""
    where_values = None
    args = [from_dt and ("time>%s", to_timestamp(from_dt)) or None,
            to_dt and ("time<%s", to_timestamp(to_dt)) or None]
    args = [arg for arg in args if arg]  # Get rid of the None values
    if args:
        where_clause = " WHERE " + " AND ".join([arg[0] for arg in args])
        where_values = tuple([arg[1] for arg in args])

    sql += where_clause + order_clause + limit_clause

    env.log.debug("get_pastes() SQL: %r (%r)" % (sql, where_values))
    cursor.execute(sql, where_values)

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

    id_is_valid = staticmethod(lambda num: 0 < int(num) <= (1L << 31))

    def __init__(self, env, id=None, title=u'', author=u'',
                 mimetype='text/plain', data=u'', time=None):
        self.env = env
        self.id = None
        self.title = title
        self.author = author
        self.mimetype = mimetype
        self.data = data
        self.time = time
        self.resource = Resource('pastebin', self.id)

        if id is not None and self.id_is_valid(id):
            row = None
            db = env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute('SELECT title, author, mimetype, data, time '
                           'FROM pastes WHERE id = %s', (id,))
            row = cursor.fetchone()
            if row:
                self.id = id
                self.title, self.author, self.mimetype, self.data, time = row
                self.time = datetime.fromtimestamp(time, utc)
            else:
                raise ResourceNotFound(_('Paste %s does not exist.' % id),
                                       _('Invalid Paste Number'))

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
        cursor.execute('DELETE FROM pastes WHERE id = %s', (self.id,))

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
            cursor.execute('INSERT INTO pastes (title, author, mimetype, '
                           'data, time) VALUES (%s, %s, %s, %s, %s)',
                           (self.title, self.author, self.mimetype, self.data,
                            to_timestamp(self.time)))
            self.id = db.get_last_id(cursor, 'pastes')
        else:
            cursor.execute('UPDATE pastes SET title=%s, author=%s, mimetype=%s,'
                           'data=%s, time=%s WHERE id = %s', (
                self.title, self.author, self.mimetype, self.data,
                to_timestamp(self.time), self.id
            ))

        if handle_ta:
            db.commit()

    def render(self, req):
        """Render the data."""
        context = Context.from_request(req)
        mimeview = Mimeview(self.env)
        return mimeview.render(context, self.mimetype, self.data,
                               annotations=['lineno'])
