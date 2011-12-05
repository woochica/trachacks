# -*- coding: utf-8 -*-

from setuptools import setup

extra = {}

try:
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:
        extra['cmdclass'] = cmdclass
        extractors = [('**.py', 'python', None),]
        extra['message_extractors'] = {
            'relevantticket': extractors,
        }
except ImportError:
    pass
                      
setup(
    name = 'RelevantTicket',
    version = '0.1',
    author = 'ONE',
    author_email = '',
    url = 'http://trac-hacks.org/wiki/RelevantTicketPlugin',
    description = """The ticket number(ex.#123) that is input in custom field is 
                     transcribed into the ticket that is specified with custom field.""",
    license = 'New BSD',
    
    packages = ['relevantticket'],
    package_data = {'relevantticket': ['locale/*/LC_MESSAGES/*.mo']},
    entry_points = {'trac.plugins': ['relevantticket = relevantticket']},
    zip_safe = True,
    **extra)
    