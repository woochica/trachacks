from setuptools import setup

setup(name="PivotalPayments", version="0.1", 
      packages=['effort_stats', 'phpdoc_link', 'wiki_restrict', 'wanted_pages'],
      package_data={'wiki_restrict' : ['htdocs/css/*.css']})