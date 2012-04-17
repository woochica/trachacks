from setuptools import find_packages, setup

extra = {}
try:
    import babel
    extra['message_extractors'] = {
        'tracworkflowadmin': [
            ('**.py', 'python', None),
            ('**.html', 'genshi', None),
        ],
    }
    from trac.util.dist import get_l10n_js_cmdclass
    extra['cmdclass'] = get_l10n_js_cmdclass()
except ImportError:
    pass

setup(
    name = 'TracWorkflowAdmin', 
    version = '0.12.0.2',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'tracworkflowadmin': [
            'templates/*.html',
            'htdocs/*.gif',
            'htdocs/css/*.css',
            'htdocs/scripts/*.js',
            'htdocs/scripts/messages/*.js',
            'htdocs/themes/*/*.css',
            'htdocs/themes/*/images/*.png',
            'locale/*.*',
            'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    entry_points = { 'trac.plugins': 'tracworkflowadmin.web_ui = tracworkflowadmin.web_ui' },

    author = 'OpenGroove,Inc.',
    author_email = 'trac@opengroove.com',
    url = 'http://trac-hacks.org/wiki/TracWorkflowAdminPlugin',
    description = 'Web interface for workflow administration of Trac',
    license = 'BSD', # the same license as Trac
    **extra)
