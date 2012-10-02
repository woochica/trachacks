
import MySQLdb
import datetime

#
# Storage for time tracking. Currently uses a MySQL database only.
#
class TimeStore:
    def __init__(self, host, user, password, database):
        self.__conn = MySQLdb.connect (host = host,
                                       user = user,
                                       passwd = password,
                                       db = database)

    def __del__(self):
        try:
            self.__conn.close()
        except:
            pass

    def update_task(self, src_id, name, tags, owner, created, updated,
                    time_worked, time_estimated, completed):
        """
        Updates a task in the store or creates a new record if the task doesn't
        already exist.
        """

        cursor = self.__conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE src_id = %s" % src_id)

        insert = cursor.rowcount == 0

        if insert:
            cursor.execute(
                """
                INSERT INTO tasks
                SET src_id = %s,
                    name = %s,
                    tags = %s,
                    owner = %s,
                    created = %s,
                    updated = %s,
                    time_worked = %s,
                    time_estimated = %s,
                    completed_on = %s
                """,
                (src_id, name, tags, owner, self._format_date(created),
                    self._format_date(updated), time_worked, time_estimated,
                    self._format_date(completed)))
        else:
            cursor.execute(
                """
                UPDATE tasks
                SET name = %s,
                    tags = %s,
                    owner = %s,
                    created = %s,
                    updated = %s,
                    time_worked = %s,
                    time_estimated = %s,
                    completed_on = %s
                WHERE src_id = %s
                LIMIT 1
                """,
                (name, tags, owner, self._format_date(created),
                    self._format_date(updated), time_worked, time_estimated,
                    self._format_date(completed), src_id))

        self.__conn.commit()

        # Fetch row id to return
        cursor.execute("SELECT task_id FROM tasks WHERE src_id = %s", src_id)
        id = 0
        try:
            id = cursor.fetchone()[0]
        except: pass

        cursor.close()

        return id

    def insert_entry(self, src_id, user, start_time, end_time, duration, tags,
                     comments, task_id):
        """
        Inserts a new time entry into the store. Doesn't check first if it
        already exists. We assume that clear_entries has previously been called
        to blow away any existing entries in the reporting date range.
        """

        if not user:
            return

        cursor = self.__conn.cursor()

        cursor.execute(
            """
            INSERT INTO times
            SET src_id = %s,
                user = %s,
                start_time = %s,
                end_time = %s,
                duration = %s,
                tags = %s,
                comments = %s,
                task_id = %s
            """,
            (src_id, user, self._format_date(start_time),
                self._format_date(end_time), duration, tags, comments,
                task_id))

        cursor.close()
        self.__conn.commit()

    def clear_entries(self, user, range_start, range_end = None):
        """
        Deletes the entries for the given user in the given date range. Note
        that the range start and end refer define the range of START times of
        the time entries. This is the SlimTimer behaviour which we mimick.
        """

        if not user:
            return

        cursor = self.__conn.cursor()

        if range_start and range_end:
            cursor.execute(
                """
                DELETE FROM times
                WHERE start_time >= %s AND start_time <= %s
                AND user = %s
                """,
                (range_start, range_end, user))
        elif range_start:
            cursor.execute(
                """
                DELETE FROM times
                WHERE start_time >= %s
                AND user = %s
                """,
                (range_start, user))
        elif range_end:
            cursor.execute(
                """
                DELETE FROM times
                WHERE start_time <= %s
                AND user = %s
                """,
                (range_end, user))

        cursor.close()
        self.__conn.commit()

    # Internal methods

    def _format_date(self, date_str):
        if not date_str or date_str == 0:
            return None # This will become NULL in MySQL

        return "%s" % date_str


