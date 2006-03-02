
from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.web.main import IRequestHandler
from trac.util import escape, Markup
from trac.wiki.api import IWikiWorkflowController
from trac.wiki.model import WikiPage

class UserbaseModule(Component):
    implements(IWikiWorkflowController)

    # IWikiWorkflowController methods
    def get_default_version(self, name):
        """Return default viewable version number for the named page.
        Called when the wiki UI is rendering a page with no 'version='
        in the HTTP request arguments.

        In this method, you'd normally do db lookups and so on to
        determine what the default viewable version of the named page
        is, and then return it; for this example, we're just going to
        pick a random page version instead.
        """
        db = self.env.get_db_cnx()
        page = WikiPage(self.env, name, 1)
        history = page.get_history(all_versions=1)
        try:
            # get highest version number
            (version,time,author,comment,ipnr) = history.next()
            # here's a twist; we can enable Wikipedia-style talk
            # pages which are *not* under workflow control 
            if name.endswith("/Talk"):
                return version
            # make some debug noise
            import random, sys
            print >>sys.stderr, "highest version", version
            # randomize the version number
            version = random.randint(1,version)
            print >>sys.stderr, "random version", version
            return version
        except:
            # returning None means that the default wiki "last edit
            # wins" behavior will be used instead
            return None

    def would_collide(self, req, name, version):
        """Return boolean or None to control collision errors.  Called
        when a user has hit "Submit" after editing a page.
        
        In this method, you can do all sorts of checks to determine if
        you want to allow this version of this page to be used as the
        base version for the edit that the user is submitting, you can
        check if there has been a new version checked in since the
        user started editing, and so on.  Return true if you want the
        user to get a collision error message, false if not.  If you
        don't care, and want to defer to trac's built-in "edit last
        version only" behavior, then return None.  In this example, we
        always return false, meaning we always allow edits of any 
        version, and never issue collision errors.
        """
        return 0

