
import re
from trac_ticket import TracTicket

class Reporter:

    def __init__(self, db, st_session, users, logger, trac_db = None):
        self.db         = db
        self.st         = st_session
        self.users      = users
        self.log        = logger
        self.trac_db    = trac_db

    def fetch_entries(self, range_start, range_end):

        # This is a mapping from src entry IDs to database entry IDs
        updated_tasks = {}

        # Get the username to use
        st_username = self.st.get_username()
        if not st_username:
            self.log.error("No trac username. Can't insert time entries "\
                           "into the database without a username.")
            return
        trac_username = self.users.get_trac_user(st_username)
        if not trac_username: trac_username = st_username

        # Clear old records in this range
        self.db.clear_entries(trac_username, range_start, range_end)
        entries = self.st.get_time_entries(range_start, range_end)
        
        for entry in entries:
            if not updated_tasks.has_key(entry.task.id):
                updated_tasks[entry.task.id] = self._update_task(entry.task)
            self.db.insert_entry(src_id = entry.id,
                            user = trac_username,
                            start_time = entry.start_time,
                            end_time = entry.end_time,
                            duration = entry.duration,
                            tags = entry.tags,
                            comments = entry.comments,
                            task_id = updated_tasks[entry.task.id])

    # Internal methods

    def _update_task(self, st_task):
        """
        Update the task in the store and trac using information from ST
        """

        # Get the estimated hours or None
        rv = self._update_trac_ticket(st_task)
        est = rv['est_hours']
        if est:
            try:
                est = float(est) * 60 * 60
            except:
                est = None

        # Update the store
        db_id = self.db.update_task(src_id = st_task.id,
                            name = st_task.name,
                            tags = ','.join(st_task.tags),
                            owner = self.users.get_trac_user(st_task.owner),
                            created = st_task.created_at,
                            updated = st_task.updated_at,
                            time_worked = st_task.hours * 60 * 60,
                            time_estimated = est,
                            completed = (None,st_task.completed_on)\
                                            [st_task.complete])

        return db_id

    def _update_trac_ticket(self, st_task):
        """
        Update the hours in trac based on the ST task
        """

        rv = { 'est_hours': None }
        
        if not self.trac_db:
            return rv

        trac_id = self._get_ticket_id(st_task.name)
        if not trac_id:
            return rv

        ticket = TracTicket(self.trac_db, trac_id)
        trac_hours = ticket.get_hours()
        if trac_hours == None:
            #
            # There's no totalhours. We probably aren't recording hours in
            # trac.  Perhaps the timingandestimationplugin could be installed.
            # In any case, just skip it.
            #
            return rv

        if abs(trac_hours - st_task.hours) >= 0.01:
            author = ticket.get_owner()
            ticket.set_hours(trac_hours, st_task.hours, author,
                             comment = "Updating ticket hours from !SlimTimer")
            self.trac_db.commit()

        rv['est_hours'] = ticket.get_est_hours()

        return rv

    def _get_ticket_id(self, str):
        """
        Parse the ticket ID from a ST task name
        """
        pat = r'^\s*#(\d+)'
        try:
            return int(re.search(pat, str).group(1))
        except:
            return 0

