"""
interfaces for listening to repository changes
and configuration of hooks
"""

from trac.core import Interface

### interfaces for subscribers

class IRepositoryHookSubscriber(Interface):
    """
    interface for subscribers to repository hooks
    """

    def is_available(repository, hookname):
        """can this subscriber be invoked on this hook?"""        

    def invoke(changeset):
        """what to do on a commit"""

### interfaces for the hook system

class IRepositoryChangeListener(Interface):
    """listeners to changes from repository hooks"""

    def type():
        """list of types of repository to listen for changes"""

    def available_hooks():
        """hooks available for the repository"""

    def changeset(repo, hookname, *args):
        """return the changeset as specified by the SCM-specific arguments"""

    def subscribers(hookname): # XXX needed? -> elsewhere?
        """returns activated subscribers for a given hook"""
        # XXX this should probably be moved, as it puts
        # the burden of knowing the subscriber on essentially
        # the repository.  This is better done in infrastructure
        # outside the repository;
        # or maybe this isn't horrible if an abstract base class 
        # is used for this interface

    def invoke_hook(repo, hookname, *args):
        """fires the given hook"""

class IRepositoryHookSetup(Interface):
    """participants capable of setting up hooks"""

    def enable(hookname):
        """enable the RepositoryChangeListener callback for a given hook"""

    def disable(hookname):
        """disable the RepositoryChangeListener callback for a given hook"""

    def is_enabled(hookname):
        """
        whether the hook has been set up;  
        contingent upon enable marking the hook in such a way that it can be identified as enabled
        """

    def can_enable(hookname):
        """
        whether the hook can be set up
        """

class IRepositoryHookAdminContributer(Interface):
    """
    contributes to the webadmin panel for the RepositoryHookSystem
    """
    # XXX there should probably an equivalent on the level of IRepositoryHookSubscribers

    def render(hookname, req):
        """extra HTML to display in the webadmin panel for the hook"""
        
    def process_post(hookname, req):
        """what to do on a POST request"""

class IRepositoryHookSystem(IRepositoryChangeListener, IRepositoryHookSetup, IRepositoryHookAdminContributer):
    """
    mixed-in interface for a complete hook system;
    implementers should be able to listen for changes (IRepositoryChangeListener)
    as well as setup the hooks (IRepositoryHookSetup)
    and contribute to the webadmin interface (IRepositoryHookAdminContributer)
    """
