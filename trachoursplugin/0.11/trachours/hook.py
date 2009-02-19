from trac.core import *

try:
    from repository_hook_system.interface import IRepositoryHookSubscriber

    class HoursHook(Component):
        """add hours to tickets via commit messages"""
        
        implements(IRepositoryHookSubscriber)

        def is_available(self, repository, hookname):
            return True

        def invoke(self, chgset):
            pass

except ImportError:
    pass
