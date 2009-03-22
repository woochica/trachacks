from setuptools import setup

PACKAGE = 'TracEditorGuide'
VERSION = '1.0'
URL = 'http://trac-hacks.org/wiki/EditorGuidePlugin'

extra = {}

try:
    import babel
    extra['message_extractors'] = {
        'traceditorguide': [
            ('**.py', 'python', None),
        ],
    }
except ImportError:
    pass

setup(  name=PACKAGE,
        install_requires='Trac >=0.12dev',
        description='Editor\'s Guide navigation item plugin for Trac 0.12',
        keywords='trac plugin navigation menu',
        version=VERSION,
        url = URL,
        license='BSD',
        author='Alexey Kinyov',
        author_email='rudy@05bit.com',
        packages=['traceditorguide'],
        long_description="""
        Plugin adds extra navigation item to '''metanav'''. This
        is a link to Editor's Guide, which is visible only for
        users who have permission to edit wiki pages.
        """,
        package_data = { 'traceditorguide': [ 'locale/*.*', 'locale/*/LC_MESSAGES/*.*' ] },
        entry_points={'trac.plugins': '%s = traceditorguide' % PACKAGE},

        **extra )