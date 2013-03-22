from setuptools import setup

# IMPORTANT: If this plugin has been deployed for development(using
#   "python setup.py develop -md ...") and this file has changed, the plugin 
#   will have to be redeployed (using the previously mentioned command). See:
#   https://svn.mayastudios.de/mtpp/wiki/TracSandbox#Deployingaself-developedplugin

# Name of the python package
PACKAGE = 'inieditorpanel'

setup(
    name = 'TracIniAdminPanel',
    version = '0.81beta',
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "https://svn.mayastudios.de/mtpp",
    
    description = "An admin panel for editing trac.ini",
    keywords = "trac plugins",
    
    license = "BSD",
    
    install_requires = [
        'Trac>=0.12',
    ],
    
    packages = [ PACKAGE ],
    package_data = { PACKAGE: [ 'templates/*', 'htdocs/*' ] },
                                     
    entry_points = { 'trac.plugins': [ 
        '%s.web_ui = %s.web_ui' % (PACKAGE, PACKAGE),
        '%s.default_manager = %s.default_manager' % (PACKAGE, PACKAGE),
        # Add additional components here
      ] },
)
