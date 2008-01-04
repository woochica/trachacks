# -*- coding: utf-8 -*-
"""
    Trac
    ~~~~

    A supybot plugin that communicates with the trac ircannouncer plugin.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import supybot

__version__ = '0.1'
__author__ = supybot.Author('Armin Ronacher', 'mitsuhiko',
                            'armin.ronacher@active-4.com')
__contributors = {}
__url__ = 'http://trac-hacks.org/wiki/IrcAnnouncerPlugin'


from Trac import config, plugin
reload(plugin)

Class = plugin.Class
configure = config.configure
