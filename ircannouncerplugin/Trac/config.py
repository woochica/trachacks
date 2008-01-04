# -*- coding: utf-8 -*-
"""
    Trac.config
    ~~~~~~~~~~~

    The plugin configuration

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
from supybot import conf, registry, callbacks


def configure(advanced):
    conf.registerPlugin('Trac', True)


class Tracs(registry.SpaceSeparatedSetOfStrings):
    List = callbacks.CanonicalNameSet


Trac = conf.registerPlugin('Trac')
conf.registerGlobalValue(Trac, 'tracs',
    Tracs([], """Determines what tracs should be enabled."""))
conf.registerGlobalValue(Trac, 'interfacePort',
    registry.PositiveInteger(53312, """The port for the bot
    interface.  The trac will connect to this port to notify the
    bot about changes."""))
conf.registerChannelValue(Trac, 'announce',
    Tracs([], """List of tracs that should be announced."""))
conf.registerChannelValue(Trac, 'defaultTrac',
    registry.String('', """The shortcut of the trac that will be
    used as default trac unless a different shortcut is provided
    in the link.  If you set this to "w" for example #42 will be
    the same as #w24."""))
