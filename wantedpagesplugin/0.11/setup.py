from setuptools import setup

setup(name="WantedPages",
      description="Lists all wiki pages that are linked to but not created",
      long_description="""
      Lists all wiki pages that are linked to but not created in wikis, ticket
      descriptions and ticket comments. Use `[[WantedPages(show_referrers)]]`
      to show referring pages.""",
      version="0.4dev",
      homepage="http://trac-hacks.org/wiki/WantedPagesPlugin",
      author="jfrancis",
      email="unkown@example.com",
      packages=['wanted_pages'],
      entry_points={
          'trac.plugins': [
              'WantedPages = wanted_pages.wanted_pages',
              ]},
      )
