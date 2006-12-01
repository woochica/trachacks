from setuptools import setup

setup(
    name='ldapwpplugin',
    description='LDAP White Pages Plugin for Trac',
    author='Herbert Valerio Riedel',
    author_email='hvr@gnu.org',
    keywords='',
    url='',
    version='0.0.1',
    license="GPL",
    long_description="",
    zip_safe=True,
    packages=['ldapwpplugin'],
    entry_points = {'trac.plugins':
                    ['git = ldapwpplugin.wp'],
                    },
    package_data={'ldapwpplugin': ['templates/*.cs']},
    data_files=[],
    install_requires=[],
    )
