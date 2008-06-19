from trac.core import *

class ISVNChangeListener(Interface):
    """interface for listeners to SVN commits"""

    def on_change(env, changeset):
        """what to do on a commit"""
