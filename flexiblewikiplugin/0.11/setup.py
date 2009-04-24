from setuptools import setup

PACKAGE = 'TracFlexWikiPlugin'
VERSION = '0.2'
URL = 'http://trac-hacks.org/wiki/FlexibleWikiPlugin'

extra = {}

try:
    import babel
    extra['message_extractors'] = {
        'tracflexwiki': [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
        ],
    }
except ImportError:
    pass

setup(  name=PACKAGE,
        install_requires='Trac >=0.11',
        description='Plugin allows to make flexible structure of wiki pages.',
        keywords='trac plugin navigation structure wiki menu',
        version=VERSION,
        url = URL,
        license='BSD',
        author='Alexey Kinyov',
        author_email='rudy@05bit.com',
        packages=['tracflexwiki'],
        long_description="""Plugin allows to make flexible structure of wiki pages. For any
of wiki pages parent page can be set up. So we get flexible structure instead of 'plain' wiki
structure. """,
        package_data = { 'tracflexwiki': [ 'htdocs/*.css', 'templates/*.html',
                        'locale/*.*', 'locale/*/LC_MESSAGES/*.*' ] },
        entry_points={'trac.plugins': '%s = tracflexwiki' % PACKAGE},

        **extra
)