from trac.core import Interface

class ITaskSorter(Interface):
    # Process task list to precompute keys or otherwise make
    # compareTasks() more efficient.
    def prepareTasks(self, ticketsByID):
        """Called to prepare tasks for sorting."""

    # Provide a compare function for sorting tasks.
    # May be used as cmp argument for sorted(), and list.sort().
    # Returns -1 if t1 < t2, 0 if they are equal, 1 if t1 > t2.
    def compareTasks(self, t1, t2):
        """Called to compare two tasks"""

class IResourceCalendar(Interface):
    # Return the number of hours available for the resource on the
    # specified date.
    # FIXME - return None if no information available?
    # FIXME - should we just pass the ticket we want to work on?  It
    # has resource (owner), estimate, etc. which might be useful to a
    # calendar.
    # FIXME - should this be pm_hoursAvailable or something so other
    # plugins can implement it without potential conflict?
    def hoursAvailable(self, date, resource = None):
        """Called to see how many hours are available on date"""

class ITaskScheduler(Interface):
    # Schedule each the ticket in tickets with consideration for
    # dependencies, estimated work, hours per day, etc.
    # 
    # Assumes tickets is a list returned by TracPM.query(). 
    #
    # On exit, each ticket has a start and finish that can be accessed
    # with TracPM.start() and finish().  No other changes are made.
    def scheduleTasks(self, options, tickets):
        """Called to schedule tasks"""

