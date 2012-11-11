# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2010-2012 Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from setuptools import find_packages, setup

extra = {}

try:
    from trac.util.dist  import  get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [
            ('**.py',                'python', None),
            ('**/templates/**.html', 'genshi', None),
            ('**/templates/**.txt',  'genshi', {
                'template_class': 'genshi.template:TextTemplate'
            }),
        ]
        extra['message_extractors'] = {'announcer': extractors}
# i18n is implemented to be optional here.
except ImportError:
    pass


setup(
    name = 'TracAnnouncer',
    version = '1.0',
    author = 'Robert Corsaro',
    author_email = 'rcorsaro@gmail.com',
    description = 'Customizable notification system for Trac',
    license = """
    Copyright (c) 2008, Stephen Hansen.
    Copyright (c) 2009, Robert Corsaro.
    All rights reserved. Released under the 3-clause BSD license.
    """,
    url = 'http://www.trac-hacks.org/wiki/AnnouncerPlugin',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {
        'announcer': [
            'htdocs/*.*',
            'htdocs/css/*.*',
            'locale/*/LC_MESSAGES/*.mo',
            'locale/.placeholder',
            'templates/*.html',
            'templates/*.txt'
        ]
    },
    install_requires = ['Genshi >= 0.5', 'Trac >= 0.11'],
    extras_require={
        'Babel': 'Babel>= 0.9.5',
        'Trac': 'Trac >= 0.12',
        'acct_mgr': 'TracAccountManager',
        'bitten': 'Bitten',
        'fullblog': 'TracFullBlogPlugin',
        'xmpp': 'xmpppy',
    },
    entry_points = {
        'trac.plugins': [
            'announcer.api = announcer.api',
            'announcer.distributors.mail = announcer.distributors.mail',
            'announcer.distributors.xmppd = announcer.distributors.xmppd[xmpp]',
            'announcer.email_decorators = announcer.email_decorators',
            'announcer.filters = announcer.filters',
            'announcer.formatters = announcer.formatters',
            'announcer.model = announcer.model',
            'announcer.pref = announcer.pref',
            'announcer.producers = announcer.producers',
            'announcer.resolvers = announcer.resolvers',
            'announcer.subscribers = announcer.subscribers',
            'announcer.util.mail = announcer.util.mail',
            'announcer.opt.acct_mgr.announce = announcer.opt.acct_mgr.announce[acct_mgr]',
            'announcer.opt.bitten.announce = announcer.opt.bitten.announce[bitten]',
            'announcer.opt.fullblog.announce = announcer.opt.fullblog.announce[fullblog]',
            'announcer.opt.subscribers = announcer.opt.subscribers',
        ]
    },
    test_suite = 'announcer.tests.test_suite',
    tests_require = [],
    **extra
)
