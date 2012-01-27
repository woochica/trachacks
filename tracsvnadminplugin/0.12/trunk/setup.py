# SVNAdmin plugin

from setuptools import setup, find_packages

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
    name = 'TracSVNAdmin', 
    version = '0.2',
    description = 'SVNAdmin for Trac',
    long_description = """
		Use the SVNAdmin plugin to administer Subversion repositories.
	""",
    author = 'Evolonix',
    author_email = 'info@evolonix.com',
    license = 'BSD',
    url = 'http://www.evolonix.com/trac/plugins/tracsvnadmin',
    download_url = 'http://www.evolonix.com/trac/plugins/tracsvnadmin',
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Version Control',
    ],
    packages = find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        svnadmin.admin = svnadmin.admin
        svnadmin.api = svnadmin.api
    """,
    package_data = {
    	'svnadmin': [
    		'templates/*.html',
    		'htdocs/css/*.css',
    		'htdocs/images/*'
    	]
    },
)