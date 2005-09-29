from trac.core import *
from trac.admin.console import IAdminConsoleProvider
import time
from discussion.core import DiscussionCore

class DiscussionConsole(Component):
    implements(IAdminConsoleProvider)

    _help_forum = [('forum list', 'Show available forums'),
                   ('forum add <name> <title> <description> <moderator> [...]', 'Add a forum'),
                   ('forum remove <name>', 'Remove a forum')]

    _help_topic = [('topic list [<forum>]', 'Show discussion topics'),
                   ('topic remove <id>', 'Remove a topic')]

    # IAdminConsoleProvider methods
    def get_console_commands(self, tracadm):
        self.tracadm = tracadm
        yield ('forum', self._help_forum, self.do_forum, self.complete_forum)
        yield ('topic', self._help_topic, self.do_topic, self.complete_topic)


    # forum ... commands
    def complete_forum(self, text, line, begidx, endidx):
        argv = self.tracadm.arg_tokenize(line)
        argc = len(argv)
        if line[-1] == ' ':
            argc += 1
        if argc == 2:
            comp = [ 'list', 'add', 'remove' ]
        return self.tracadm.word_complete(text, comp)

    def do_forum(self, line):
        arg = self.tracadm.arg_tokenize(line)
        try:
            if arg[0] == 'list':
                self._do_forum_list()
            elif arg[0] == 'add':
                if len(arg) < 5: raise Exception('Insufficient arguments')
                self._do_forum_add(*arg[1:])
            elif arg[0] == 'remove':
                if len(arg) != 2: raise Exception('Invalid number of arguments')
                self._do_forum_remove(arg[1])
            else:
                self.tracadm.do_help('forum')
        except Exception, e:
            print 'Forum %s failed:' % arg[0], e

    def _do_forum_list(self):
        rows = self.tracadm.db_query("SELECT name, subject, moderators FROM forum ORDER BY name")
        self.tracadm.print_listing(['Name', 'Title', 'Moderators'], rows)

    def _do_forum_add(self, name, subject, description, *moderators):
        moderators = ' '.join(moderators)
        self.tracadm.db_update('''
            INSERT INTO forum
                (name, time, moderators, subject, description)
            VALUES
                ('%s', %i, '%s', '%s', '%s')''' % (name, int(time.time()), moderators, subject, description))
        print 'Added forum "%s"' % name

    def _do_forum_remove(self, name):
        row = self.tracadm.db_query("SELECT id FROM forum WHERE name='%s'" % name)
        if not row:
            raise Exception('No such forum "%s"' % name)
        id = row.next()[0]
        self.tracadm.db_query('DELETE FROM message WHERE forum=%s' % id)
        self.tracadm.db_query('DELETE FROM topic WHERE forum=%s' % id)
        self.tracadm.db_update('DELETE FROM forum WHERE id=%s' % id)
        print 'Removed forum "%s"' % name

    # topic ... commands
    def complete_topic(self, text, line, begidx, endidx):
        argv = self.tracadm.arg_tokenize(line)
        argc = len(argv)
        if line[-1] == ' ':
            argc += 1
        if argc == 2:
            comp = [ 'list', 'remove' ]
        return self.tracadm.word_complete(text, comp)

    def do_topic(self, line):
        arg = self.tracadm.arg_tokenize(line)
        try:
            if arg[0] == 'list':
                if len(arg) > 2: raise Exception('Invalid number of arguments')
                self._do_topic_list(*arg[1:])
            elif arg[0] == 'remove':
                if len(arg) != 2: raise Exception('Invalid number of arguments')
                self._do_topic_remove(arg[1])
            else:
                self.tracadm.do_help('topic')
        except Exception, e:
            print 'Topic %s failed:' % arg[0], e

    def _do_topic_list(self, forum = None):
        rows = self.tracadm.db_query("SELECT (SELECT name FROM forum WHERE forum.id = topic.forum) subject, author FROM topic ORDER BY time")
        self.tracadm.print_listing(['Name', 'Subject', 'Author'], rows)

    def _do_topic_remove(self, topic):
        pass
