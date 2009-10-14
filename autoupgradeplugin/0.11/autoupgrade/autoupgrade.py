"""
AutoUpgrade:
a plugin for Trac
http://trac.edgewall.org
"""

import os
import sys
import trac.env

from trac.core import *
from trac.env import *
from trac.util.text import exception_to_unicode
from trac.util.translation import _

class AutoUpgrade(Component):

    implements(trac.env.IEnvironmentSetupParticipant)

    ### methods for IEnvironmentSetupParticipant

    """Extension point interface for components that need to participate in the
    creation and upgrading of Trac environments, for example to create
    additional database tables."""

    def environment_created(self):
        """Called when a new Trac environment is created."""

    def environment_needs_upgrade(self, db):
        """Called when Trac checks whether the environment needs to be upgraded.
        
        Should return `True` if this participant needs an upgrade to be
        performed, `False` otherwise.
        """
        return False

    def upgrade_environment(self, db):
        """Actually perform an environment upgrade.
        
        Implementations of this method should not commit any database
        transactions. This is done implicitly after all participants have
        performed the upgrades they need without an error being raised.
        """



# horrible monkey patching

def open_environment(env_path=None, use_cache=False):
    # XXX copy and paste the god-damned code 
    # might as well write FORTRAN at this point
    """Open an existing environment object, and verify that the database is up
    to date.

    @param env_path: absolute path to the environment directory; if ommitted,
                     the value of the `TRAC_ENV` environment variable is used
    @param use_cache: whether the environment should be cached for subsequent
                      invocations of this function
    @return: the `Environment` object
    """
    global env_cache, env_cache_lock

    if not env_path:
        env_path = os.getenv('TRAC_ENV')
    if not env_path:
        raise TracError(_('Missing environment variable "TRAC_ENV". '
                          'Trac requires this variable to point to a valid '
                          'Trac environment.'))

    env_path = os.path.normcase(os.path.normpath(env_path))
    if use_cache:
        env_cache_lock.acquire()
        try:
            env = env_cache.get(env_path)
            if env and env.config.parse_if_needed():
                # The environment configuration has changed, so shut it down
                # and remove it from the cache so that it gets reinitialized
                env.log.info('Reloading environment due to configuration '
                             'change')
                env.shutdown()
                if hasattr(env.log, '_trac_handler'):
                    hdlr = env.log._trac_handler
                    env.log.removeHandler(hdlr)
                    hdlr.close()
                del env_cache[env_path]
                env = None
            if env is None:
                env = env_cache.setdefault(env_path, open_environment(env_path))
        finally:
            env_cache_lock.release()
    else:
        env = Environment(env_path)
        needs_upgrade = False
        try:
            needs_upgrade = env.needs_upgrade()
        except Exception, e: # e.g. no database connection
            env.log.error("Exception caught while checking for upgrade: %s",
                          exception_to_unicode(e, traceback=True))
        if needs_upgrade:

            if env.is_component_enabled(AutoUpgrade):
                try:
                    env.upgrade(backup=True)
                except TracError, e:
                    env.upgrade()
            else:
                raise TracError(_('The Trac Environment needs to be upgraded.\n\n'
                                  'Run "trac-admin %(path)s upgrade"',
                                  path=env_path))

    return env

trac.env.open_environment = open_environment

