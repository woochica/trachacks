from setuptools import find_packages, setup

version='0.1.1'

setup(name='RepositoryHookSystem',
      version=version,
      description="plugin to make repository commit events iterable and accessible to other plugins",
      author='Jeff Hammel',
      author_email='jhammel@openplans.org',
      url='http://trac-hacks.org/wiki/k0s',
      keywords='trac plugin',
      license="GPL",
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests*']),
      include_package_data=True,
      package_data={'repository_hook_system': [ 'templates/*']},
      zip_safe=False,
      install_requires=['python-dateutil'],
      entry_points = """
      [trac.plugins]
      repositoryhooksystem = repository_hook_system
      """,
      )

