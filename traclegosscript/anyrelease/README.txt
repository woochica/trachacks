= TracLegos =

[ this is a work in progress;  this is more of a roadmap than a README ]

TracLegos is software designed to assist with trac project creation.  
The idea is that project templates may be created according to project
type and need.
Its goal is to make project creation easy and flexible, allowing
flexibility with regards to creation methodology as well as
extensibility as a project factory for environments with advanced
needs.  TracLegos is not [at least by design, yet] meant for project
upgrading or maintainence, but only to setup a project with sensible
defaults. 

TracLegos can be invoked in a number of ways:

 * through a command-line interface (legos.py)

 * through a WSGI wrapper around trac (web.py)

 * via `paster create`

 * programmatically

Different methods of invocation are differently important to different
environments. TracLegos (in {{{legos.py}}}) is meant to be the "head"
of the octopus, and ideally will do little else but coordinate the
other moving parts.


== trac project configuration ==

Typical trac project configuration consists of:

 * a trac.ini file

 * plugins required for the project

 * a repository 

 * a database [TODO]

 * permissions, groups, milestones, etc that live in the database [TODO]

TracLegos abstracts this to:

 * a list of templates to be applied in order

 * requirements files to be installed via PoachEggs

 * site configuration (an .ini file) controlling how project creation
   is done

 * site variables to be applied to all projects

The templates use the form ${variable} to denote variables.  The
templates can be .ini files or the can be PasteScript templates.  In
the latter case, the templates may also contain requirements files and
other information and procedures to be applied when they are invoked.


== TracProject templates ==

TracProject, a PasteScript template, is used and proposed as the de
facto manner for sharing project configuration.  In its minimal form,
a TracProject subclass need contain only a template directory with
`conf/trac.ini` and the variables (vars) in the class needed for that
file. However, the general form of the template is also suited to more
complex tasks.

PasteScript was chosen as the vessel for trac project configuration
for several reasons:

 * it is the tried + tested de facto python standard for filesystem
   templates

 * it is easy to construct a basic template with just the trac.ini
   file, but since python is used, projects could do any complex task
   necessary for project creation

 * there is already the notion of defined variables (var) 

 * other niceities

In short, a PasteScript template is both sufficient to hold the notion
of a project in trac and has infrastructure valuable to TracLegos

The PasteScript template model may also be easily extended to
accompany additional needs [though some refactoring of PasteScript may
prove necessary].

A TracProject template typically contains:

  * a template with a `conf/trac.ini` and potentially other files

  * variables needed for interpolation of this file

  * requirements files for the plugins the project need

  * any other code required for executation to make the template

Tools may be provided [TODO] that convert a user's trac.ini file into
a TracProject template (and will do so with a PasteScript template).

PasteScript may also be used to create projects instead of TracLegos.
[I'm not sure if running PasteScript will be fully capable of doing
all the steps that TracLegos does.  Worth investigating.]


== Web Interface ==

TracLegos also provides a web interface to project creation which
provides a custom index.html file and allows TTW project creation for
authorized individuals [authorization TBD...in fact, most of the web
interface TBD].  The project creation as viewed TTW is as follows:

 * Initial project creation:  project name, logo, and type of project.
   The type of project is chosen from a drop-down menu that contains
   all TracProject templates by default though this can be customized
   with site-configuration.

 * Project details: svn repository setup and mirroring, database type,
   mailing lists ... other things along these lines could go here
   too.  These are things that are important to how trac works but
   that trac itself doesn't provide front-ends to their setup.
   [These are presumedly customized too;  for instance, you could have
   site configuration that said 'always use a mysql DB', 'always make
   a new SVN repo', 'always use the existing SVN repo', etc.  The idea
   being that the TTW view allows most anything that can be done but
   that sites can (and should) lock it down to enforce consistency]

 * Project variables:  The project creator fills in any variables
   customized by the templates

Other optional steps (setup of groups, invitations to join, etc) could
be done after this, but these are the minimum required for project
creation. Upon successful creation, the viewer is redirected to the
admin page for their project [maybe with some indication of things
they might want to do next and how to find information on how to do
them].

A site configuration file can be pointed to in the .ini file used for
`paster serve`.  Additional configuration and overrides may also be
defined in this .ini file.


== Project Creation Procedure ==

For each project, the following steps are applied:

 * database creation

 * the {{{trac.ini}}} templates (both PasteScrpt and other) are munged
   together, site-wide templates applied at the end (they override)

 * the munged configuration is checked for missing variables and these
   missing variables are sought (via PasteScript or TTW)

 * the project is created

 * repository setup

 * the PasteScript templates are invoked

 * [TODO] any inherited/master configuration is updated

 * [TODO] the project is upgraded

 * [TODO] addition of groups, milestones, and other database items

[See `traclegos/legos.py` for details]
