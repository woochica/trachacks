from setuptools import setup

setup(name='TracCustomFieldAdmin',
      version='0.2.7',
      packages=['customfieldadmin'],
      author='CodeResort.com & Optaros.com',
      description='Admin panel for managing Trac ticket custom fields.',
      url='http://trac-hacks.org/wiki/CustomFieldAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': [
            'customfieldadmin.api = customfieldadmin.api',
            'customfieldadmin.customfieldadmin = customfieldadmin.customfieldadmin']},
      package_data={'customfieldadmin' : ['htdocs/css/*.css','htdocs/js/*.js', 'templates/*.html', ]},
      exclude_package_data={'': ['tests/*']},
      test_suite = 'customfieldadmin.tests.test_suite',
      tests_require = [],
      install_requires = [])

