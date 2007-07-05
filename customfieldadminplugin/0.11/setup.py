from setuptools import setup

setup(name='TracCustomFieldAdmin',
      version='0.1',
      packages=['customfieldadmin'],
      author='CodeResort.com & Optaros.com',
      description='Expose ticket custom fields using Trac 0.10 config option API',
      url='http://trac-hacks.org/wiki/CustomFieldAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': [
		    'customfieldadmin.api = customfieldadmin.api',
		    'customfieldadmin.customfieldadmin = customfieldadmin.customfieldadmin']},
      package_data={'customfieldadmin' : ['htdocs/css/*.css','htdocs/js/*.js', 'templates/*.cs', ]},
      install_requires=['TracWebAdmin'])
