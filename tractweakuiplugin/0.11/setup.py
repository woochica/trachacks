from setuptools import find_packages, setup

setup(
    name = 'TracTweakUI',
    version = '0.1',
    packages = ['tractweakui'],
    package_data = { 'tractweakui': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },
    include_package_data = True,
    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "Trac Tweak UI plugin for Trac.",
    license = "BSD",
    keywords = "trac tweak ui",
    url = "http://trac-hacks.org/wiki/TracTweakUiPlugin",
    classifiers = [
        'Framework :: Trac',
    ],
    install_requires = [],
    entry_points = {'trac.plugins': ['tractweakui = tractweakui.web_ui']},
)