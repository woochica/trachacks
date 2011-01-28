import time

class Timer(object):
    """Intended for loops that should timeout eventually."""
    
    def __init__(self, duration):
        """'duration' should in seconds (an int)."""
        self.duration = int(duration)
        self.start()
    
    def start(self):
        """Starts (or restarts) the timer."""
        self.started = int(time.time())
        
    @property
    def running(self):
        """Returns true while the time since starting the timer has not
        exceeded the duration."""
        return int(time.time()) - self.started < self.duration
