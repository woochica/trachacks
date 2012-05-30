#!/usr/bin/env python
from setuptools import setup, find_packages

PACKAGE = 'WSGITrac'
VERSION = '0.4'

setup(
    name=PACKAGE, version=VERSION,
    description='Trac WSGI plugin',
    author="Martin Paljak", author_email="martin@paljak.pri.ee",
    license='GPL', url='http://www.trac-hacks.org/wiki/TracWsgiPlugin',
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
    zip_safe=True,
    include_package_data=True,
    install_requires = [
            'setuptools>=0.6c5',
            'Trac>=0.11dev',
            'PasteDeploy',
            'Genshi'
        ],
    entry_points = {
        'trac.plugins': [
            'wsgiplugin.wsgiplugin = wsgiplugin.wsgiplugin'
        ],
        'paste.app_factory': [
            'main = wsgiplugin.wsgiplugin:wsgi_trac',
            'trac = wsgiplugin.wsgiplugin:wsgi_trac',
            'tracs = wsgiplugin.wsgiplugin:wsgi_tracs',
            'permanent_redirect = wsgiplugin.wsgiplugin:permanent_redirect',
            'temporary_redirect = wsgiplugin.wsgiplugin:temporary_redirect'
        ]
    }
)
