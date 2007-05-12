import enum
from trac.db import Table, Column, Index

EventPriority = enum.Enum ("normal", "important")
EventType = enum.Enum ("public", "protected", "private")

class Event:
    _schema = [
        Table('azcalendar_event', key='id')[
            Column('id', auto_increment=True),
            Column('author'),
            Column('time_insert', type='int'),
            Column('time_update', type='int'),
            Column('time_begin', type='int'),
            Column('time_end', type='int'),
            Column('type', type='int'),
            Column('priority', type = 'int'),
            Column('title'),
            Index(['time_begin']),
            Index(['time_end']),
        ]
    ]

    def __init__ (self, xid, author, insert, modify, begin, end, xtype, priority, title):
        import time
        self._id_ = xid
        self._author_ = author
        self._time_insert_ = insert
        self._time_update_ = modify
        self._time_begin_ = begin
        self._time_end_ = end
        self._type_ = xtype
        self._priority_ = priority
        self._title_ = title

    def get_id (self):
        return self._id_

    def get_author (self):
        return self._author_

    def get_time_update (self):
        return self._time_update_

    def get_time_insert (self):
        return self._time_insert_

    def get_time_begin (self):
        return self._time_begin_

    def get_time_end (self):
        return self._time_end_

    def get_title (self):
        return self._title_

    def get_priority (self):
        return self._priority_

    def get_type (self):
        return self._type_

    def set_priority (self, priority):
        self._priority_ = priority

    def set_type (self, evtype):
        self._type_ = evtype

    def set_title (self, title):
        self._title_ = title

    def set_author (self, author):
        self._author_ = author

    def set_time_end (self, time_end):
        self._time_end_ = time_end

    def set_time_begin (self, time_begin):
        self._time_begin_ = time_begin

    def set_time_update (self, time_update):
        self._time_update_ = time_update


    def get_event (cls, env, evid):
        """
        Load event with given `evid' from database.
        """

        db = env.get_db_cnx()
        cursor = db.cursor()
        sql = "SELECT * FROM azcalendar_event WHERE id = \"%s\"" % evid
        cursor.execute ( sql )
        row = cursor.fetchone()
        return Event(*tuple([i for i in row]))

    get_event = classmethod(get_event)


    def update(self, env, req):
        """
        Update database values of this event.
        """

        db = env.get_db_cnx()
        cursor = db.cursor()
        try:
            sql = """
            UPDATE azcalendar_event set
            author = \"%s\",
            time_insert =%s,
            time_update =%s,
            time_begin =%s,
            time_end =%s,
            type= %s,
            priority = %s,
            title = \"%s\" where id = %s
            """ % ( self._author_,self._time_insert_, self._time_update_ ,
                        self._time_begin_,  self._time_end_ , self._type_ ,self._priority_, self._title_, self._id_ )
            req.hdf['sql'] = sql
            cursor.execute(sql)
            db.commit()
            return 'redirect.cs', None
        except:
            req.hdf['azcalendar.reason'] = "Database failure."
            return 'azerror.cs', None

    def save (self, env, req):
        """
        Add this event into database.
        """

        db = env.get_db_cnx()
        cursor = db.cursor()
        try:
            sql = """
            INSERT INTO azcalendar_event
            (author,
            time_insert, time_update, time_begin, time_end,
            type, priority, title)
            VALUES
            (\"%s\",
            %s, %s, %s, %s,
            %s, %s, "%s" )
            """ % (self._author_, self._time_insert_, self._time_update_,
                   self._time_begin_, self._time_end_ , self._type_, self._priority_, self._title_)
            cursor.execute(sql)
            db.commit()
            return 'redirect.cs', None
        except:
            req.hdf['azcalendar.reason'] = "Database failure."
            return 'azerror.cs', None

    def delete (self, env):
        """
        Delete this event from database.
        """

        db = env.get_db_cnx()
        cursor = db.cursor()
        try:
            sql = "DELETE FROM azcalendar_event WHERE id = \"%s\"" % self._id_
            cursor.execute(sql)
            db.commit()
            return 'redirect.cs', None
        except:
            req.hdf['azcalendar.reason'] = "Database failure."
            return 'azerror.cs', None


    def parse_row (cls, row):
        """
        Given a `row', which is a `SELECT * FROM azcalendar_evnet'
        tuple, create new Event instance from that row.
        """

        T = lambda x:x
        types = [int, T, int, int, int, int, int, int, T]
        init = [t(v) for t, v in zip(types, row)]
        return Event(*init)

    parse_row = classmethod(parse_row)


    def events_between (cls, env, stamp1, stamp2, user):
        """
        Given a time window <stamp1, stamp2), return all events that
        are visible through that window.  This includes also events
        that are not entirely contained in the window.
        """

        import time

        db = env.get_db_cnx()
        cursor = db.cursor()
        if user == "admin":
            selector = ""
        else:
            selector = "(type=0 OR author=\'%s\') AND" % user

        sql = """
        SELECT *
        FROM azcalendar_event
        WHERE %(selector)s
          (time_end >= %(time_beg)s AND time_begin < %(time_end)s)
          OR (time_begin < %(time_beg)s AND time_end >= %(time_end)s )
        """ % {'time_beg' : int(stamp1),
               'time_end' : int(stamp2),
               'selector' : selector}
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [Event.parse_row (row) for row in rows]

    events_between = classmethod(events_between)

