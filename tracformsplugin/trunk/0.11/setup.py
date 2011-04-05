# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

try:
    from trac.util.dist  import  get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
        ]
        extra['message_extractors'] = {
            'tracforms': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


VERSION = '0.3'

setup(
    name = 'TracForms',
    description = 'Universal form provider for tickets and wiki',
    version = VERSION,
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    maintainer = 'Steffen Hoffmann',
    maintainer_email = 'hoff.st@web.de',
    url = 'http://trac-hacks.org/wiki/TracFormsPlugin',
    license = 'GPL',
    packages = ['tracforms'],
    package_data = {
        'tracforms': [
            'locale/*/LC_MESSAGES/*.mo', 'locale/.placeholder',
        ]
    },
    zip_safe = True,
    install_requires = ['Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    entry_points = {
        'trac.plugins': [
            'tracforms.api = tracforms.api',
            'tracforms.macros = tracforms.macros',
            'tracforms.web_ui = tracforms.web_ui',
        ]
    },
    **extra
)
