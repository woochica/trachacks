# -*- coding: utf-8 -*-
"""
    Trac.plugin
    ~~~~~~~~~~~

    A supybot plugin that communicates with the trac ircannouncer plugin.

    :copyright: Copyright 2008 by Armin Ronacher.
    :license: BSD.
"""
import new
from threading import Thread
from urlparse import urljoin
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy, Fault
from supybot import callbacks, conf, registry, world, ircmsgs, log
from supybot.utils.str import format, ellipsisify
from supybot.ircutils import bold, underline
from supybot.commands import *


class TracProxy(object):

    def __init__(self, url, callback):
        self.url = url
        self._callback = callback

    def __getattr__(self, name):
        if name.startswith('__'):
            return self
        return TracProxy(self.url, getattr(self._callback, name))

    def __call__(self, *args):
        try:
            return self._callback(*args)
        except Fault, e:
            if e.faultCode == 50:
                raise ResourceNotFound()
            raise TracError(str(e))
        except Exception, e:
            raise TracError('Could not connect to trac: %s' % e)
        raise DispatchEnd()


class XMLRPCServer(SimpleXMLRPCServer, Thread):

    def __init__(self, connector, start=True):
        port = connector.registryValue('interfacePort')
        Thread.__init__(self)
        SimpleXMLRPCServer.__init__(self, ('127.0.0.1', port))
        self.register_instance(self)
        self.connector = connector
        self.running = True
        if start:
            self.start()

    def _dispatch(self, name, args):
        if name not in self.connector.rpcMethods:
            raise TypeError('no such method')
        try:
            return self.connector.rpcMethods[name](*args)
        except Fault:
            raise
        except:
            log.exception('Unhandled exception in Trac XMLRPC:')
            raise

    def run(self):
        while self.running:
            self.handle_request()

    def stop(self):
        self.server_close()
        self.running = False
        try:
            server = ServerProxy('http://%s:%d' % self.server_address)
            server.ping()
        except:
            pass


class TracError(Exception):
    pass


class ResourceNotFound(TracError, LookupError):
    pass


class Trac(callbacks.PrivmsgCommandAndRegexp):
    threaded = True
    regexps = ['ticketRegexp', 'changesetRegexp']
    commands = ['ticket', 'changeset', 'add', 'remove', 'announce',
                'denounce']

    def __init__(self, irc):
        self.__parent = super(Trac, self)
        self.__parent.__init__(irc)
        self.tracs = callbacks.CanonicalNameDict()
        for name in self.registryValue('tracs'):
            self._addTrac(name, None)
        self.rpcMethods = {
            'ircannouncer.notify':      self._onRemoteNotify,
            'ircannouncer.ping':        lambda: 'OK'
        }
        self.xmlrpc = XMLRPCServer(self)

    # Dispatching Methods

    def callCommand(self, command, irc, msg, *args, **kwargs):
        try:
            self.__parent.callCommand(command, irc, msg, *args, **kwargs)
        except TracError, e:
            if e.message:
                irc.error(e.message)

    def listCommands(self):
        commands = set(self.commands)
        commands.update(self.tracs.keys())
        return sorted(commands)

    def isCommandMethod(self, name):
        return name in self.commands or name in self.tracs

    def getCommandMethod(self, command):
        try:
            return self.__parent.getCommandMethod(command)
        except AttributeError:
            return self.makeTracCommand(command[0])

    def makeTracCommand(self, trac):
        def func(self, irc, msg, args):
            if len(args) < 2 or args[0] not in self.commands:
                raise callbacks.ArgumentError()
            getattr(self, args[0])(irc, msg, args[1:] + [trac])
        func.__name__ = trac
        func.__doc__ = """\
        <action> <arg1>, [<arg2>[, ...]]

        Convenience function to output related information for the %s trac.
        "%s ticket 2" does exactly the same as "ticket 2 %s".
        """ % (trac, trac, trac)
        return new.instancemethod(func, self, self.__class__)

    def die(self):
        self.xmlrpc.stop()

    # Regular Expression Callbacks

    def ticketRegexp(self, irc, msg, match):
        r"(?:\b([a-zA-Z_]+):)?(?:\bticket:|#)([0-9]+)|#([a-zA-Z]+)([0-9]+)"
        for idx in xrange(1, 4, 2):
            trac_name, ticket_id = match.group(idx, idx + 1)
            if ticket_id:
                self._ticketLink(irc, msg, trac_name, int(ticket_id),
                                 silent=True)

    def changesetRegexp(self, irc, msg, match):
        r"""(?x)
            (?:\b([a-zA-Z_]+):)?\bchangeset:([0-9a-fA-F]+(?::[0-9a-fA-F]*)?) |
            \B\[([a-zA-Z]+)?([0-9]+)\]"""
        for idx in xrange(1, 4, 2):
            trac_name, changeset_id = match.group(idx, idx + 1)
            if changeset_id:
                self._changesetLink(irc, msg, trac_name, changeset_id,
                                    silent=True)

    # Regular Callbacks

    def ticket(self, irc, msg, args, ticket_id, trac_name):
        """<ticket id> [<trac>]

        Gets the summary of the ticket provided and the link to it.  If the
        trac is not given, the channel's default trac is used.
        """
        self._ticketLink(irc, msg, trac_name, ticket_id, silent=False)
    ticket = wrap(ticket, ['int', optional('commandName')])

    def changeset(self, irc, msg, args, ticket_id, trac_name):
        """<changeset id> [<trac>]

        Gets the summary of the changeset provided and the link to it.  If the
        trac is not given, the channel's default trac is used.
        """
        self._changesetLink(irc, msg, trac_name, changeset_id, silent=False)
    changeset = wrap(changeset, [('regexpMatcher', '/^[a-fA-F0-9:]+$/'),
                                 optional('commandName')])

    def add(self, irc, msg, args, trac_name, trac_url):
        """<trac name> <trac url>

        Add a new trac to the database.  The name should be a short
        word specifying the name of the trac (for example "py", "trac"
        etc.) or one letter if you want to use the short forms."""
        self._addTrac(trac_name, trac_url)
        irc.reply('Added trac at %s as "%s"' % (trac_url, trac_name))
    add = wrap(add, ['commandName', 'httpUrl'])

    def remove(self, irc, msg, args, trac_name):
        """<trac name>

        Remove a new trac to the database."""
        if trac_name not in self.tracs:
            irc.error('Unknown trac "%s".' % trac_name)
        else:
            self._removeTrac(trac_name)
            irc.reply('Removed "%s".' % trac_name)
    remove = wrap(remove, ['commandName'])

    def announce(self, irc, msg, args, channel, trac_name):
        """[<channel>] <trac name>

        Announce the trac in the channel."""
        url = self._getTracURL(irc, msg, trac_name, silent=False)
        self.registryValue('announce', channel).add(trac_name)
        irc.reply('The trac %s at %s will now be announced in %s' % (
                  trac_name, url, channel))
    announce = wrap(announce, ['channel', 'commandName'])

    def denounce(self, irc, msg, args, channel, trac_name):
        """[<channel>] <trac name>

        Stop announcing a trac in a channel."""
        if trac_name in self.tracs:
            announced_tracs = self.registryValue('announce', channel)
            if trac_name in announced_tracs:
                announced_tracs.discard(trac_name)
                irc.reply('I\'m not announcing "%s" in %s any longer' % (
                          trac_name, channel))
            else:
                irc.error('I\'m not annoucing "%s" in %s!' % (
                          trac_name, channel))
        else:
            irc.error('Sorry, I don\'t know "%s" yet' % trac_name)
    denounce = wrap(denounce, ['channel', 'commandName'])

    # Helper methods

    def _ticketLink(self, irc, msg, trac_name, ticket_id, silent=False):
        try:
            trac = self._openTrac(irc, msg, trac_name, silent)
            for line in self._printTicket(trac.getTicket(ticket_id)):
                irc.reply(line, prefixNick=False)
        except ResourceNotFound:
            if not silent:
                irc.error('No such ticket')

    def _changesetLink(self, irc, msg, trac_name, changeset_id, silent=False):
        try:
            trac = self._openTrac(irc, msg, trac_name, silent)
            for line in self._printChangeset(trac.getChangeset(changeset_id)):
                irc.reply(line, prefixNick=False)
        except ResourceNotFound:
            if not silent:
                irc.error('No such ticket')

    def _onRemoteNotify(self, type, values):
        trac = self._findTracByURL(values['trac']['url'])
        if trac is None:
            return 1
        handler = {
            'changeset':        self._printChangeset,
            'ticket':           self._printTicket
        }[type]
        for irc, channel in self._findAnnouncementChannels(trac):
            for line in handler(values, detailed=True):
                irc.sendMsg(ircmsgs.privmsg(channel, line))
        return 0

    def _printChangeset(self, values, detailed=False):
        yield format('%s [%s] by %s in %s (%n): %s',
            bold('Changeset'),
            values['rev'],
            underline(values['author']),
            values['path'],
            (values['file_count'], 'file'),
            ellipsisify(values['message'].strip(), 130)
        )
        yield '<%s>' % values['url']

    def _printTicket(self, values, detailed=False):
        action = values.get('action')
        if action is not None:
            if action == 'created':
                action = 'created by %s' % underline(values['reporter'])
            elif action == 'changed':
                action = 'changed by %s' % underline(values['author'])
            action = ' (%s)' % action
        yield format('%s #%s: %s%s',
            bold('Ticket'),
            values['id'],
            values['summary'],
            action or ''
        )
        yield '<%s>' % values['url']

    def _findTracByURL(self, trac_url):
        trac_url = trac_url.rstrip('/')
        for name, url in self.tracs.iteritems():
            if url.rstrip('/') == trac_url:
                return name

    def _findAnnouncementChannels(self, trac):
        group = conf.supybot.plugins.Trac.announce
        for irc in world.ircs:
            for channel in irc.state.channels:
                if trac in group.get(channel)():
                    yield irc, channel

    def _openTrac(self, irc, msg, trac_name, silent=False):
        trac_url = self._getTracURL(irc, msg, trac_name, silent)
        proxy = ServerProxy(urljoin(trac_url, 'ircannouncer_service'))
        return TracProxy(trac_url, proxy.ircannouncer)

    def _getTracURL(self, irc, msg, name, silent=True):
        if name is None:
            channel = irc.isChannel(msg.args[0]) and msg.args[0] or None
            name = self.registryValue('defaultTrac', channel)
            if not name:
                if len(self.tracs) == 1:
                    name = self.tracs.keys()[0]
                else:
                    if silent:
                        return
                    raise TracError('Could not find a default trac for '
                                    'the channel but multiple tracs are '
                                    'defined.')
        if name in self.tracs:
            url = self.tracs[name]
            if not url.endswith('/'):
                url += '/'
            return url
        if not silent:
            raise TracError('No trac for the name "%s"' % name)

    def _addTrac(self, name, url):
        self.registryValue('tracs').add(name)
        group = self.registryValue('tracs', value=False)
        if url is None:
            try:
                url = self.registryValue(registry.join(['tracs', name]))
            except registry.NonExistentRegistryEntry:
                return
        self.tracs[name] = url
        group.register(name, registry.String(url, ''))

    def _removeTrac(self, name):
        self.tracs.pop(name, None)
        conf.supybot.plugins.Trac.tracs().remove(name)
        try:
            conf.supybot.plugins.Trac.tracs.unregister(name)
        except registry.NonExistentRegistryEntry:
            pass


Class = Trac
