from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='SettingsPlugin', 
    version='0.6.0',
    author = 'Franz Mayer, Gefasoft AG',
    author_email = 'franz.mayer@gefasoft.de', 
    description = 'Provides commands for removing unneeded milestones, components, etc. and setting a bunch of config option from file.',
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'http://trac-hacks.org/wiki/SettingsPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        settingsplugin = settingsplugin
    """
)

