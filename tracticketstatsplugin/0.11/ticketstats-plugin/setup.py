from setuptools import find_packages, setup

setup(
	name='Tracticketsats', version='1.0',
	packages=find_packages(exclude=['*.test*']),
	entry_points = """
		[trac.plugins]
		ticketstats = ticketstats
	""",
	package_data={'ticketstats': ['templates/*.cs']},
)


