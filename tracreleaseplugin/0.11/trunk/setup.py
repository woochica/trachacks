# -*- coding: utf-8 -*-

from setuptools import find_packages, setup


setup(name='TracReleasePlugin',
        version='0.2',
        packages = ['tracrelease', 'tracrelease.db'],
        description="Release Control",
        author='Joao Alexandre de Toledo',
        author_email='tracrelease@toledosp.com.br',
        url='http://trac-hacks.org/wiki/TracReleasePlugin',
        keywords='trac plugin',
        license="",
        packages=['tracrelease', 'tracrelease.db'],
        package_data={'tracrelease' : ['templates/*.html', 'htdocs/*']},
        include_package_data=True,
        zip_safe=False,
        install_requires = [''],
        entry_points = {
            'trac.plugins': [
                'TracRelease.core = tracrelease.core',
                'TracRelease.setup = tracrelease.init'
            ]
        },
    )