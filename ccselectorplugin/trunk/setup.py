# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

PACKAGE = 'cc_selector'

try:
    from trac.util.dist import get_l10n_js_cmdclass
    cmdclass = get_l10n_js_cmdclass()
    if cmdclass:
        # includes some 'install_lib' overrides,
        # i.e. 'compile_catalog' before 'bdist_egg'
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'genshi', None),
        ]
        extra['message_extractors'] = {
            PACKAGE: extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


VERSION = '0.0.3'

setup(
    name = PACKAGE,
    version = VERSION,
    description = 'Visual Cc ticket field editor for Trac',
    keywords = 'trac cc ticket editor',
    url = 'http://trac-hacks.org/wiki/CcSelectorPlugin',
    author = 'Vladislav Naumov',
    author_email = 'vnaum@vnaum.com',
    license = 'GPL',
    maintainer = 'Steffen Hoffmann',
    maintainer_email = 'hoff.st@web.de',
    packages = [PACKAGE],
    package_data = {PACKAGE: [
        'htdocs/*.js', 'htdocs/lang_js/*.js', 'locale/*/LC_MESSAGES/*.mo',
        'locale/.placeholder', 'templates/*.html'
        ]},
    zip_safe = True,
    entry_points = {
        'trac.plugins': [
            'cc_selector.cc_selector = cc_selector.cc_selector'
        ]},
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    **extra
    )
