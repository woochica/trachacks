from setuptools import find_packages, setup

version='1.1'

setup(name='EarnedValuePlugin',
      version=version,
      description="Generates earned value charts based on Trac tickets",
      author='MSOE SDL Team',
      author_email='bladornr@msoe.edu',
      maintainer='MSOE SDL Team',
      maintainer_email='bladornr@msoe.edu',
      keywords='trac plugin',
      zip_safe=False,
      packages=['earnedValue'],
      install_requires=['Trac >= 0.12',
	      		'python-dateutil',
			'GChartWrapper'],
      entry_points="""
      [trac.plugins]
      earnedValue.EVMacro = earnedValue.EVMacro
      """
      )

