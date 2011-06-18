from setuptools import setup

setup(name="TracWikiMenuPlugin",
      version="0.0.1",
      packages = ['tracwikimenu'],
      author="Bangyou Zheng", 
      author_email="zheng.bangyou@gmail.com", 
      url="http://trac-hacks.org/wiki/TracWikiMenuPlugin",
      description="Show menus for WIKI pages based on wikitoolsplugin",
      license="BSD",
      entry_points={'trac.plugins': [
            'tracwikimenu = tracwikimenu']},
      package_data={'tracwikimenu' : [
           'htdocs/css/*.css',
           'htdocs/js/*.js']}
)
