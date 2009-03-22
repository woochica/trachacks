from setuptools import setup

PACKAGE = 'TracEditorGuide'
VERSION = '1.0'
URL = 'http://trac-hacks.org/wiki/EditorGuidePlugin'

setup(  name=PACKAGE,
        install_requires='Trac >=0.11',
        description='Editor\'s Guide navigation item plugin for Trac 0.11',
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
        entry_points={'trac.plugins': '%s = traceditorguide' % PACKAGE},
)
