from setuptools import setup

setup(
    name = 'TracMacroConfigPlugin',
    version = '0.2',
    packages = ['tracmacroconfig'],

    author = 'Patrick "bof" Schaaf',
    author_email = 'trachacks@bof.de',
    description = '''Help Plugins/Macros with trac.ini option inheritance''',
    url = 'http://trac-hacks.org/wiki/TracMacroConfigPlugin',
    license = 'GPLv2',

    entry_points = {
        'trac.plugins': [
            'tracmacroconfig.examplemacro = tracmacroconfig.examplemacro',
        ],
    }

    install_requires = ['Trac >= 0.11.7'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: Trac',
    ],
)
