from setuptools import find_packages, setup

version='0.1'

setup(name='SimpleTracProject',
      version=version,
      description="Simple Trac Project Template",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac project template',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      install_requires = [ 'PasteScript', 
                           'TracLegos',
                           'TracAccountManager',
                           'TracCustomFieldAdmin',
                           'TracDateField',
                           'TracIncludeMacro',
                           'IniAdmin',
                           'TracPermRedirect',
                           'TracTags',
                           'AutocompleteUsers',
                           'SVN_URLs',
                           'Tracbacks',
                           ],
      dependency_links = [
      "http://trac-hacks.org/svn/traclegosscript/anyrelease#egg=TracLegos",
      "http://trac-hacks.org/svn/accountmanagerplugin/trunk#egg=TracAccountManager",
      "http://trac-hacks.org/svn/customfieldadminplugin/0.11#egg=TracCustomFieldAdmin",
      "http://trac-hacks.org/svn/datefieldplugin/0.11#egg=TracDateField",
      "http://trac-hacks.org/svn/includemacro/0.11#egg=TracIncludeMacro",
      "http://trac-hacks.org/svn/iniadminplugin/0.11#egg=IniAdmin",
      "http://trac-hacks.org/svn/permredirectplugin/0.11#egg=TracPermRedirect",
      "http://trac-hacks.org/svn/tagsplugin/tags/0.6#egg=TracTags",

      # plugins with TOPP authors
      "http://trac-hacks.org/svn/autocompleteusersplugin/0.11#egg=AutocompleteUsers",
      "http://trac-hacks.org/svn/svnurlsplugin/0.11#egg=SVN_URLs",
      "http://trac-hacks.org/svn/tracbacksplugin/0.11#egg=Tracbacks",
      ],
      zip_safe=False,
      entry_points = """
      [paste.paster_create_template]
      simple_project = simple.project:SimpleTracProject
      """,
      )

