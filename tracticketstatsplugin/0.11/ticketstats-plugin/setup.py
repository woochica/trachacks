from setuptools import find_packages, setup

setup(
	name='Tracticketstats', version='2.1',
	packages=find_packages(exclude=['*.test*']),
	entry_points = """
		[trac.plugins]
		ticketstats = ticketstats
	""",
	package_data={'ticketstats': ['templates/*.html']},
)


