
from setuptools import find_packages, setup


extra = {}

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


PACKAGE = 'DataSaverPlugin'
VERSION = '2.0'

setup(
    name=PACKAGE,
    description='Restore previously unsafed data after re-entering a form.',
    version=VERSION,
    author='Rich Harkins',
    author_email='rich@worldsinfinite.com',
    license='GPL', url='http://trac-hacks.org/wiki/DataSaverPlugin',
    install_requires = ['Babel>= 0.9.5', 'Trac >= 0.12dev'],
    packages=find_packages(exclude=['*.tests*']),
    package_data={'datasaver': ['htdocs/*.js', 'htdocs/lang_js/*.js',
                                'htdocs/*.css', 'locale/*/LC_MESSAGES/*.mo']},
    entry_points="""
        [trac.plugins]
        datasaver = datasaver.datasaver
    """,
    **extra
)

