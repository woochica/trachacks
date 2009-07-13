from setuptools import find_packages, setup

version='0.2.1'

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

                           # trac wiki macros
                           'TracIncludeMacro',
                           'TracProgressMeterMacro',
                           'TracRedirect',
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
                           'TracTags',
                           'TracTicketDelete',

                           # plugins with TOPP authors
                           'AutocompleteUsers',
                           'icalexporter',
                           'SVN_URLs',
                           'Tracbacks',
                           'svnsyncplugin'],
      dependency_links = [
      "http://trac-hacks.org/svn/traclegosscript/anyrelease#egg=TracLegos",

      # wiki macros
      "http://trac-hacks.org/svn/includemacro/0.11#egg=TracIncludeMacro",
      "http://trac-hacks.org/svn/progressmetermacro/0.11#egg=TracProgressMeterMacro",
      "http://svn.ipd.uka.de/repos/javaparty/JP/trac/plugins/redirect-0.11#egg=TracRedirect",
      "http://trac-hacks.org/svn/tocmacro/0.11#egg=TracTocMacro",

      # plugins
      "http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager",
      "http://trac-hacks.org/svn/customfieldadminplugin/0.11#egg=TracCustomFieldAdmin",
      "http://trac-hacks.org/svn/datefieldplugin/0.11#egg=TracDateField",
      "http://trac-hacks.org/svn/graphvizplugin/0.11/#egg=graphviz",
      "http://trac-hacks.org/svn/iniadminplugin/0.11#egg=IniAdmin",
      "http://trac-hacks.org/svn/masterticketsplugin/0.11#egg=TracMasterTickets",
      "http://trac-hacks.org/svn/permredirectplugin/0.11#egg=TracPermRedirect",
      "http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags",
      "http://trac-hacks.org/svn/ticketdeleteplugin/0.11#egg=TracTicketDelete",

      # plugins with TOPP authors
      "http://trac-hacks.org/svn/autoupgradeplugin/0.11#egg=AutoUpgrade",
      "http://trac-hacks.org/svn/autocompleteusersplugin/0.11#egg=AutocompleteUsers",
      "http://trac-hacks.org/svn/icalexporterplugin/0.11#egg=icalexporter",
      "http://trac-hacks.org/svn/svnurlsplugin/0.11#egg=SVN_URLs",
      "http://trac-hacks.org/svn/tracbacksplugin/0.11#egg=Tracbacks",
      "http://trac-hacks.org/svn/svnsyncplugin/0.11#egg=svnsyncplugin"
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      oss_project = osstracproject.project:OSSTracProject
      """,
      )

