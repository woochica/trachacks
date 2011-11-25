from setuptools import find_packages, setup

# name can be any name.  This name will be used to create the .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name='XMailPlugin', 
    version='0.4.1',
    author = 'Gefasoft AG, Franz Mayer', 
    description = 'Extented Mail Plugin (XMail)',
    long_description = """XMail plugin allows to send user-specific, timed (periodically executed) notifications of new / changed tickets """,
    url = 'http://www.gefasoft-muenchen.de',
    download_url = 'http://trac-hacks.org/wiki/MailPlugin',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        xmail = xmail
    """,
    package_data={'xmail': ['templates/*.*',
                               'htdocs/css/*.css', 
                               'htdocs/js/*.js', 
                               'locale/*.*',
                               'locale/*/LC_MESSAGES/*.*']}
     # , 'default-pages/*'
)