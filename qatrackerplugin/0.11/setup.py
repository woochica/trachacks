from setuptools import find_packages, setup

# name can be any name.  This name will be used to create .egg file.
# name that is used in packages is the one that is used in the trac.ini file.
# use package name as entry_points
setup(
	name         = 'QATracker',
	version      = '0.1-alpha',
	author       = 'Rob Weigel',
	author_email = 'jahoonigan31-at-gmail-dot-com',
	description  = 'QA Test Case management via TRAC',
	license      = 'http://www.opensource.org/licenses/bsd-license.php',
	packages=find_packages(exclude=['*.tests*']),
	entry_points = """
		[trac.plugins]
		qatracker = qatracker
	""",
	package_data={'qatracker': ['templates/*.html', 
								 'htdocs/css/*.css', 
								 'htdocs/images/*']},
)
