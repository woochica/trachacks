from setuptools import setup

extra = {}

from trac.util.dist import get_l10n_cmdclass
cmdclass = get_l10n_cmdclass()
if cmdclass:
    extra['cmdclass'] = cmdclass
    extractors = [
        ('*.py',                 'python', None),
        ('**/templates/**.html', 'genshi', None),
    ]
    extra['message_extractors'] = {
        'customfieldadmin': extractors,
    }

setup(name='TracCustomFieldAdmin',
      version='0.2.8',
      packages=['customfieldadmin'],
      author='CodeResort.com & Optaros.com',
      description='Admin panel for managing Trac ticket custom fields.',
      url='http://trac-hacks.org/wiki/CustomFieldAdminPlugin',
      license='BSD',
      entry_points={'trac.plugins': [
            'customfieldadmin.api = customfieldadmin.api',
            'customfieldadmin.customfieldadmin = customfieldadmin.customfieldadmin']},
      exclude_package_data={'': ['tests/*']},
      test_suite = 'customfieldadmin.tests.test_suite',
      tests_require = [],
      package_data={'customfieldadmin' : ['htdocs/css/*.css',
                               'htdocs/js/*.js',
                               'templates/*.html', 
                               'locale/*/LC_MESSAGES/*.mo',]},
      install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
      extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
      **extra
 )

