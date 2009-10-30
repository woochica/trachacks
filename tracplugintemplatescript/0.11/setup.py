from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='TracPluginTemplate',
      version=version,
      description="paste template for a trac plugin",
      long_description="""\
""",
      classifiers=[], # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      keywords='trac plugin template',
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      package_data={'': 
        [ 'template/+package+/*/*', 'template/+package+/*.py_tmpl', 'template/*.py_tmpl' ]},
      zip_safe=False,
      install_requires=[ 'PasteScript', ],
      entry_points="""
      # -*- Entry points: -*-
      [paste.paster_create_template]
      trac_plugin = trac_plugin_skel:TracPluginSkelTemplate
      """,
      )
      
