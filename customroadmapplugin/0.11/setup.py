from setuptools import setup


setup(name = 'TracCustomRoadmap',
      version = '0.4',
      author='Dave Cole',
      author_email='djc@object-craft.com.au',
      license='BSD',
      url='http://www.object-craft.com.au/~djc',
      description='Plugin to provide a configurable roadmap in Trac.',
      keywords='trac plugin roadmap',
      packages=['customroadmap'],
      package_data = { '': ['templates/*'] },
      entry_points={ 'trac.plugins': 'CustomRoadmap = customroadmap' },
)
