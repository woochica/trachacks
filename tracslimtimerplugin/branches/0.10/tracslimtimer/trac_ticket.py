
import time

#
# Wrapper around a trac ticket
#
class TracTicket:

    def __init__(self, db, id):
        """
        Ctor
        """
        self.db = db
        self.id = id

    ###########################################################################
    #
    # API
    #
    ###########################################################################

    def get_hours(self):
        """
        Get the total hours worked.
        """
        result = self._get_custom_field_value('totalhours')
        if not result:
            return None

        try:
            hours = float(result)
        except:
            return None

        return hours

    def set_hours(self, prev_hours, new_hours, author, change_time = None,
                  comment = None):
        """
        Set the total hours worked.
        """

        prev_hours = str(prev_hours)
        new_hours = str(new_hours)

        self._save_custom_field_value('totalhours', new_hours)
        self._save_ticket_change(author, 'totalhours', prev_hours,
                                 new_hours, change_time, comment)

    def get_est_hours(self):
        """
        Get the estimated number of hours for the ticket.
        """

        result = self._get_custom_field_value('estimatedhours')
        if not result:
            return None

        try:
            hours = float(result)
        except:
            return None

        return hours

    def get_owner(self):
        """
        Get the owner of the ticket.
        """

        cursor = self.db.cursor();
        cursor.execute("SELECT owner FROM ticket WHERE id=%s", (self.id,))

        row = cursor.fetchone()
        if not row:
            return None

        return row[0]

    def set_st_id(self, prev_id, new_id, author, change_time = None,
                  comment = None):
        """
        Get the SlimTimer ID for the ticket.
        """

        prev_id = str(prev_id)
        new_id  = str(new_id)

        self._save_custom_field_value('slimtimer_id', new_id)
        self._save_ticket_change(author, 'slimtimer_id', prev_id, new_id,
                                 change_time, comment)

    ###########################################################################
    #
    # Internal methods
    #
    ###########################################################################

    def _get_custom_field_value(self, field):
        """
        Get the value of a ticket field that is a custom field.
        """

        cursor = self.db.cursor();
        cursor.execute("SELECT value FROM ticket_custom "
                       "WHERE ticket=%s and name=%s", (self.id, field))

        row = cursor.fetchone()
        if not row:
            return None

        return row[0]

    # The following code is courtesy of timingandestimationplugin.

    def _save_custom_field_value(self, field, value):
        """
        Save the value of a ticket field that is a custom field.
        """

        cursor = self.db.cursor();
        cursor.execute("SELECT * FROM ticket_custom "
                       "WHERE ticket=%s and name=%s", (self.id, field))

        if cursor.fetchone():
            cursor.execute("UPDATE ticket_custom SET value=%s "
                           "WHERE ticket=%s AND name=%s",
                           (value, self.id, field))

        else:
            cursor.execute("INSERT INTO ticket_custom (ticket,name,value)"
                           "VALUES(%s,%s,%s)",
                           (self.id, field, value))
       
    def _save_ticket_change(self, author, field, oldvalue,
                            newvalue, change_time = None, comment = None):
        """
        Save a ticket change record.
        """

        if not change_time:
            change_time = time.time()

        change_time = str(change_time)

        cursor = self.db.cursor();
        sql = """SELECT * FROM ticket_change 
                 WHERE ticket=%s and author=%s and time=%s and field=%s"""
        cursor.execute(sql, (self.id, author, change_time, field))

        if cursor.fetchone():
            cursor.execute(
                   """UPDATE ticket_change  SET oldvalue=%s, newvalue=%s
                   WHERE ticket=%s and author=%s and time=%s and field=%s""",
                   (oldvalue, newvalue, self.id, author, change_time, field))
        else:
            cursor.execute(
                   """INSERT INTO ticket_change
                   (ticket,time,author,field, oldvalue, newvalue)
                   VALUES(%s, %s, %s, %s, %s, %s)""",
                   (self.id, change_time, author, field, oldvalue, newvalue))

            if comment:
                cursor.execute(
                       """INSERT INTO ticket_change
                       (ticket,time,author,field, oldvalue, newvalue)
                       VALUES(%s, %s, %s, %s, %s, %s)""",
                       (self.id, change_time, author, 'comment', '', comment))

