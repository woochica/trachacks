from setuptools import find_packages, setup

version='0.0'

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
      zip_safe=False,
      entry_points = """
      [trac.plugins]
      repositoryhooksystem = repository_hook_system
      """,
      )

