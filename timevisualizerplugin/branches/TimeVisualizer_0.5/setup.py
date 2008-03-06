from setuptools import setup

import tractimevisualizerplugin
plugin = tractimevisualizerplugin

setup(\
    name='TracTimeVisualizerPlugin',
    version=plugin.__version__,
    description='A plugin to render burndown graphs from ticket history',
    author=plugin.__author__,
    author_email='th07@homepelko.com',
    license=plugin.__license__,
    packages=['tractimevisualizerplugin'],
    url=plugin.__url__,
    entry_points={'trac.plugins': ['tractimevisualizerplugin.pluginwrapper=tractimevisualizerplugin.pluginwrapper']})
