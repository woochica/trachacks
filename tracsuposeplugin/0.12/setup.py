from setuptools import setup

extra = {}

try:
    from trac.util.dist  import  get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            'tractags': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


setup(name='TracSupose',
      version='0.0.1',
      packages=['tracsupose'],
      package_data={'tracsupose' : [
        'templates/*.html']},
      author='Bangyou Zheng',
      maintainer='Bangyou Zheng',
      maintainer_email='zheng.bangyou@gmail.com',
      url="http://trac-hacks.org/wiki/TracSupose",
      license='BSD',
      scripts=['update-index'],
      entry_points = {'trac.plugins': ['tracsupose = tracsupose']},
	  **extra)
