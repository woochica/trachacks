from setuptools import find_packages, setup

version='0.2.2'

setup(name='OSSTracProject',
      version=version,
      description="Open Source Software Project Trac Template",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac project OSS',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'PasteScript', 
                           'TracLegos',
                           'feedparser', # for the RSS embed macro, http://trac-hacks.org/ticket/5943

                           # trac wiki macros
                           'TracIncludeMacro',
                           'TracProgressMeterMacro',
                           'TracRedirect',
                           'TracRssEmbed',
                           'TracTocMacro',

                           # trac plugins
                           'graphviz',
                           'AutoUpgrade',
                           'IniAdmin',
                           'TracAccountManager',
                           'TracCustomFieldAdmin',
                           'TracDateField',
                           'TracMasterTickets',
                           'TracPermRedirect',
                           'TracReposReadMePlugin',
                           'TracTags',
                           'TracTicketDelete',
                           'TracWikiRename',

                           # plugins with TOPP authors
                           'AutocompleteUsers',
                           'CaptchaAuth',
                           'ComponentDependencyPlugin',
                           'ContactInfo',
                           'icalexporter',
                           'mail2trac',
                           'SVN_URLs',
                           'TicketSidebarProvider',
                           'Tracbacks',
                           'TracSQLHelper',
                           ],
      dependency_links = [
      "http://trac-hacks.org/svn/traclegosscript/anyrelease#egg=TracLegos",

      # wiki macros
      "http://trac-hacks.org/svn/includemacro/0.11#egg=TracIncludeMacro",
      "http://trac-hacks.org/svn/progressmetermacro/0.11#egg=TracProgressMeterMacro",
      "http://svn.ipd.uka.de/repos/javaparty/JP/trac/plugins/redirect-0.11#egg=TracRedirect", # weird place for it
      "http://trac-hacks.org/svn/rssembedmacro/0.11#egg=TracRssEmbed",
      "http://trac-hacks.org/svn/tocmacro/0.11#egg=TracTocMacro",

      # plugins
      "http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager",
      "http://trac-hacks.org/svn/customfieldadminplugin/0.11#egg=TracCustomFieldAdmin",
      "http://trac-hacks.org/svn/datefieldplugin/0.11#egg=TracDateField",
      "http://trac-hacks.org/svn/graphvizplugin/0.11/#egg=graphviz",
      "http://trac-hacks.org/svn/iniadminplugin/0.11#egg=IniAdmin",
      "http://trac-hacks.org/svn/masterticketsplugin/0.11#egg=TracMasterTickets",
      "http://trac-hacks.org/svn/permredirectplugin/0.11#egg=TracPermRedirect",
      "http://trac-hacks.org/svn/reposreadmeplugin/0.11#egg=TracReposReadMePlugin",
      "http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags",
      "http://trac-hacks.org/svn/ticketdeleteplugin/0.11#egg=TracTicketDelete",
      "http://trac-hacks.org/svn/wikirenameplugin/0.11/#egg=TracWikiRename",

      # plugins with TOPP authors
      "http://trac-hacks.org/svn/autoupgradeplugin/0.11#egg=AutoUpgrade",
      "http://trac-hacks.org/svn/autocompleteusersplugin/0.11#egg=AutocompleteUsers",
      "http://trac-hacks.org/svn/icalexporterplugin/0.11#egg=icalexporter",
      "http://trac-hacks.org/svn/mailtotracplugin/0.11#egg=mail2trac",
      "http://trac-hacks.org/svn/svnurlsplugin/0.11#egg=SVN_URLs",
      "http://trac-hacks.org/svn/tracbacksplugin/0.11#egg=Tracbacks",
      "http://trac-hacks.org/svn/captchaauthplugin/0.11#egg=CaptchaAuth",
      "http://trac-hacks.org/svn/contactinfoplugin/0.11#egg=ContactInfo",
      "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
      "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
      "http://trac-hacks.org/svn/tracsqlhelperscript/0.11#egg=TracSQLHelper",
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      oss_project = osstracproject.project:OSSTracProject
      """,
      )

