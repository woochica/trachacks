def layout (events, start_rounder = None, end_rounder = None):
    """
    Calendar layout.  Takes a bunch of events defined by start and end
    stamps, and distributes them into several lines, so that no events
    in one line overlap.
    """

    if not start_rounder: start_rounder = lambda x:x
    if not end_rounder: end_rounder = lambda x:x

    events = list (events)
    events.sort (lambda a, b: cmp (a.get_time_begin(), b.get_time_begin()))

    class Line:
        def __init__ (self):
            self.cursor = 0
            self.events = []

    lines = []

    for ev in events:
        start_time = start_rounder (ev.get_time_begin())
        end_time = end_rounder (ev.get_time_end())

        # Look if there is a line whose last filled cell is before
        # start_time of this event.  If there are more, choose the
        # tightest fit.
        lines.sort (lambda a, b: cmp (a.cursor, b.cursor))
        found = None
        for l in lines:
            if l.cursor <= start_time:
                found = l
            else:
                break

        # No line fits?  Add new!
        if not found:
            found = Line ()
            lines.append (found)

        # Enter the event into the line.
        found.cursor = end_time
        found.events.append (ev)

    ret = [l.events for l in lines]
    ret.sort (lambda l1, l2: cmp (l1[0].get_time_begin(), l2[0].get_time_begin()))
    return ret
