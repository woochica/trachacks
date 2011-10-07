
from setuptools import find_packages, setup


extra = {}

try:
    from trac.util.dist import get_l10n_js_cmdclass
    cmdclass = get_l10n_js_cmdclass()
    if cmdclass:
        # includes some 'install_lib' overrides,
        # i.e. 'compile_catalog' before 'bdist_egg' 
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py', 'python', None),
        ]
        extra['message_extractors'] = {
            'datasaver': extractors,
        }
# i18n is implemented to be optional here
except ImportError:
    pass


PACKAGE = 'DataSaverPlugin'
VERSION = '2.0'

setup(
    name=PACKAGE,
    description='Restore previously unsafed data after re-entering a form.',
    version=VERSION,
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    maintainer = 'Steffen Hoffmann',
    maintainer_email = 'hoff.st@web.de',
    license='GPL', url='http://trac-hacks.org/wiki/DataSaverPlugin',
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    extras_require = {'Babel': 'Babel>= 0.9.5', 'Trac': 'Trac >= 0.12'},
    packages=find_packages(exclude=['*.tests*']),
    package_data={'datasaver': ['htdocs/*.js', 'htdocs/lang_js/*.js',
                                'htdocs/*.css', 'locale/*/LC_MESSAGES/*.mo',
                                'locale/.placeholder']},
    entry_points="""
        [trac.plugins]
        datasaver = datasaver.datasaver
    """,
    **extra
)

