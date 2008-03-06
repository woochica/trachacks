from setuptools import setup

import tractimevisualizerplugin
plugin = tractimevisualizerplugin

setup(\
    name='TracTimeVisualizerPlugin',
    version=plugin.__version__,
    description='A plugin for rendering burndown images, depends timing and estimation plugin',
    author=plugin.__author__,
    author_email='',
    license=plugin.__license__,
    packages=['tractimevisualizerplugin'],
    url=plugin.__url__,
    entry_points={'trac.plugins': ['tractimevisualizerplugin.pluginwrapper=tractimevisualizerplugin.pluginwrapper']})
