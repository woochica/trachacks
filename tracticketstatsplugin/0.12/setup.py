from setuptools import find_packages, setup

setup(
	name='Tracticketstats', 
	version='2.1.1',
	maintainer = 'Ryan J Ollos',
	maintainer_email = 'ryano@physiosonics.com',
	packages=find_packages(exclude=['*.test*']),
	entry_points = """
		[trac.plugins]
		ticketstats = ticketstats
	""",
	install_requires = ['Trac >= 0.12'],
	package_data={'ticketstats': ['templates/*.html']},
)


