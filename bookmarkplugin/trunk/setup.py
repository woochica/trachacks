from setuptools import setup

setup(
    name='TracBookmark',
    version='0.1',
    packages=['tracbookmark'],
    package_data={'tracbookmark' : [
        'templates/*.html', 'htdocs/*.*', 'htdocs/js/*.js', 'htdocs/css/*.css']},
    exclude_package_data={'': ['tests/*']},
    test_suite = 'tracbookmark.tests.suite',
    author='Yoshiyuki Sugimoto',
    maintainer = 'Yoshiyuki Sugimoto',
    maintainer_email = 's.yosiyuki@gmail.com',
    license='BSD',
    url='http://trac-hacks.org/wiki/BookmarkPlugin',
    description='A plugin bookmark Trac resources.',
    entry_points = {'trac.plugins': ['tracbookmark = tracbookmark']},
    )
