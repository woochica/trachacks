from setuptools import find_packages, setup

version='0.2.1'

setup(name='GeoTrac',
      version=version,
      description="Geo Trac Project Template",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/TracLegosScript',
      keywords='trac project template',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'PasteScript',
                           'psycopg2', 
                           'TracLegos',

                           # general Trac plugins
                           'IniAdmin',
                           'TracAccountManager',
                           'TracCustomFieldAdmin',
                           'TracDateField',
                           'TracIncludeMacro',
                           'TracPermRedirect',
                           'TracTags',
                           'TracVote',
                           'TracWikiRename',

                           # TOPP-authored Trac plugins
                           'AutocompleteUsers',
                           'CaptchaAuth',
                           'GeoTicket',
                           'ImageTrac',
                           'LoomingClouds',
                           'mail2trac',
                           'SVN_URLs',
                           'Tracbacks',
                           ],
      dependency_links = [
      # PIL - needed for ImageTrac
      "http://dist.repoze.org/PIL-1.1.6.tar.gz",

      # geopy - needed for GeoTicket
      "http://geopy.googlecode.com/svn/branches/reverse-geocode#egg=geopy-0.93dev",

      # Trac plugins
      "http://trac-hacks.org/svn/traclegosscript/0.11#egg=TracLegos",
      "http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager",
      "http://trac-hacks.org/svn/customfieldadminplugin/0.11#egg=TracCustomFieldAdmin",
      "http://trac-hacks.org/svn/datefieldplugin/0.11#egg=TracDateField",
      "http://trac-hacks.org/svn/includemacro/0.11#egg=TracIncludeMacro",
      "http://trac-hacks.org/svn/iniadminplugin/0.11#egg=IniAdmin",
      "http://trac-hacks.org/svn/permredirectplugin/0.11#egg=TracPermRedirect",
      "http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags",
      "http://trac-hacks.org/svn/voteplugin/0.11#egg=TracVote",
      "http://trac-hacks.org/svn/wikirenameplugin/0.11/#egg=TracWikiRename",

      # plugins with TOPP authors
      "http://trac-hacks.org/svn/autocompleteusersplugin/0.11#egg=AutocompleteUsers",
      "http://trac-hacks.org/svn/autoupgradeplugin/0.11#egg=AutoUpgrade",
      "http://trac-hacks.org/svn/svnurlsplugin/0.11#egg=SVN_URLs",
      "http://trac-hacks.org/svn/tracbacksplugin/0.11#egg=Tracbacks",
      "http://trac-hacks.org/svn/loomingcloudsplugin/0.11#egg=LoomingClouds",
      "http://trac-hacks.org/svn/geoticketplugin/0.11#egg=GeoTicket",
      "http://trac-hacks.org/svn/imagetracplugin/0.11#egg=ImageTrac",
      "http://trac-hacks.org/svn/mailtotracplugin/0.11#egg=mail2trac",
      "http://trac-hacks.org/svn/customfieldproviderplugin/0.11#egg=CustomFieldProvider",
      "http://trac-hacks.org/svn/ticketsidebarproviderplugin/0.11#egg=TicketSidebarProvider",
      "http://trac-hacks.org/svn/captchaauthplugin/0.11#egg=CaptchaAuth",
      "http://trac-hacks.org/svn/tracsqlhelperscript/anyrelease#egg=TracSQLHelper",
      "http://trac-hacks.org/svn/componentdependencyplugin/0.11#egg=ComponentDependencyPlugin",
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      geotrac = geotrac.project:GeoTracProject
      """,
      )

