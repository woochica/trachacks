from setuptools import setup, find_packages
import sys, os

setup(name='TracQuickPluginTemplateScript',
      version='0.1',
      description="Another paste template for a trac plugin, like TracPluginTemplateScript",
      classifiers=[],
      keywords='trac plugin template script',
      author='Richard Liao',
      author_email='richard.liao.i@gmail.com',
      url='http://trac-hacks.org/wiki/TracPluginTemplate',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      package_data={'': [
        'template/*.*',
        'template/+package_code+/*.*',
        'template/+package_code+/*/*.*',
        ]},
      zip_safe=False,
      install_requires=['PasteScript',],
      entry_points="""
      # -*- Entry points: -*-
      [paste.paster_create_template]
      trac_quick_plugin = quickplugin:TracQuickPluginTemplate
      """,
      )
