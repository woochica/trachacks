== Description ==

SvnChangeListenerPlugin turns the SVN post-commit-hook into an
Extension Point, so that arbitrary plugins can act on changset
commits.  The guts of the plugin are abstracted from
http://trac.edgewall.org/browser/trunk/contrib/trac-post-commit-hook
 and the included TicketChanger plugin is a port from the
 trac-post-commit-hook as well that plays nice with the
 SvnChangeListenerPlugin pluggable architecture.

In order to plug in to SvnChangeListenerPlugin, you must import and
implement the svnchangelistener.interface.ISVNChangeListener
interface, which consists only of an on_change function that takes a
trac environment and the changeset object as arguments.

== Installation == 

The plugin and various components must be enabled for the project in
the normal fashion.  In addition, an appropriate line must be added to
the SVN post-commit-hook file:

{{{
python /path/to/svnchangelistener/listener.py -p projectname1 [-p projectname2] [...] -r "$2"
}}}

A front end to this is available in the webadmin interface, assuming
the file is writable.  Assuming TRAC_ADMIN access, browse to
{{{/admin/svn/changelistener}}} (or click on "Change Listener" it in
the SVN section of the webadmin left sidebar).  If there is no
post-commit-hook yet for the repository, an option will be availble to
install a new script (with possibly overly generous permissions, 755).
If there is already a post-commit-hook (including one made by this
plugin!), the option is given to append a bash-syntax line to the
file.  In either case, the file may be edited before form submission.

Probably a better manner should be used to configure the SVN post-commit-hook, possibly interfacing with http://trac-hacks.org/wiki/TracSvnPoliciesPlugin

== Evaluation == 

The SvnChangeListenerPlugin makes the contributted post-commit-hook
into a pluggable system without any loss of generality.  So its a win
there.  However, there are currently several short-comings, to be
ticketed:

 * ''envelope'' (http://trac.edgewall.org/browser/trunk/contrib/trac-post-commit-hook#L92) has been disabled

 * optionally, the project name should be required in the ticket regex, so that {{{fixes mytrac:#2}}} closes ticket 2 but {{{fixes #2}}} does not (useful for multiple tracs, one repo)

 * the post-command-hook should be installable from the command line

 * the webadmin installer should be smarter in figuring out if the plugin is already installed

 * more Option-based customization could be done in TicketChanger

 * handling of other commit hooks (pre-commit, etc)

 * better editting of hooks;  I think the correct solution is showing
   the hooks in a textarea providing an interface to hook into.  This
   could look like

{{{
class HookContributer(Interface):

      def hook():
      	  """name(s) of hooks to contibute to"""

      def name():
      	  """name of the contributor;  this will be added to the hook
      	  with

### ${name} Trac hook
${commandline}

	  so that the hooks can be removed and installed reliably
	  without overlapping.  Maybe a format for command line could
	  be asserted so that this could be parsed too;  i'm thinking
	  multiple projects
	  """

     def commandline(<arguments>):
          """the command line to be added"""
}}}
