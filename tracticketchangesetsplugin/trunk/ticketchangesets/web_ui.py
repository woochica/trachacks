# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Mikael Relbe
# All rights reserved.
#
# This file is licensed as described in the file COPYING that is
# distributed with Trac 0.12 from Edgewall Software. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# These components are based on code from:
#   * The tracopt/ticket/commit_updater.py script, distributed with Trac 0.12
#     from Edgewall Software (see copyright notice below).
#   * ticket_clone.py by Christian Boos, at
#     http://trac-hacks.org/wiki/CloneTicketPlugin
# ----------------------------------------------------------------------------

from genshi.builder import tag
from genshi.filters import Transformer

from trac.core import *
from trac.config import BoolOption
from trac.mimeview.api import Context
from trac.util.compat import any
from trac.versioncontrol import RepositoryManager
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from trac.web.api import ITemplateStreamFilter
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.macros import WikiMacroBase

from ticketchangesets.api import TicketChangesets
from ticketchangesets.commit_updater import CommitTicketUpdater
from ticketchangesets.translation import _, init_translation


class TicketChangesetsMacro(WikiMacroBase):
    """Insert all changesets referencing a ticket into the output.
    
    This macro must be called using wiki processor syntax as follows:
    {{{
    [[TicketChangesets(ticket)]]
    where ticket is a ticket id
    }}}
    """
    
    def __init__(self):
        init_translation(self.env.path)
    
    def expand_macro(self, formatter, name, content, args={}):
        if args:
            tkt_id = args.get('ticket')
        else:
            tkt_id = content
        changesets = TicketChangesetsFormatter(self.env, formatter.context,
                                               tkt_id, hint='inline')
        return changesets.format()


class ViewTicketChangesets(Component):
    """View changesets referencing the ticket in a box on the ticket page.
    
    Changesets are presented just above the description.
    """
    
    collapsed = BoolOption('ticket-changesets', 'collapsed', 'false',
        """Show section on ticket page as initially collapsed.""")
    
    compact = BoolOption('ticket-changesets', 'compact', 'true',
        """Make compact presentation of revision ranges, for example ![1-3]
        instead of ![1] ![2] ![3].""")
    
    hide_when_none = BoolOption('ticket-changesets', 'hide_when_none', 'false',
        """Hide section on ticket page when no changesets relates to the
        ticket.""")
    
    implements(ITemplateStreamFilter)

    def __init__(self):
        init_translation(self.env.path)

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists:
                context = Context.from_request(req, ticket.resource)
                self.changesets = TicketChangesetsFormatter(self.env, context,
                                                            ticket.id)
                exists = self.changesets.exists()
                if exists or not self.hide_when_none:
                    filter = Transformer('//div[@id="attachments"]')
                    return stream | filter.after(self._render(req, ticket,
                                                              exists))
        return stream

    def _render(self, req, ticket, exists):
        if exists:
            message = self.changesets.format()
            return tag.div(tag.h2(_("Repository Changesets"),
                                  class_='foldable'),
                           tag.div(message, id='changelog'),
                           class_=self.collapsed and 'collapsed')
        else:
            message = _("(none)")
            return tag.div(tag.h2(_("Repository Changesets"), ' ', message,
                                  class_='foldable'))


class TicketChangesetsFormatter(object):
    """Return formatted changesets for presentation in a ticket section or
    inlined wiki.
    """

    def __init__(self, env, context, tkt_id, hint='ticket'):
        self.env = env
        self.context = context
        self.tkt_id = tkt_id
        self.hint = hint
        self.compact =  env.config.getbool('ticket-changesets', 'compact')
        self.changesets = TicketChangesets(env).get(tkt_id)

    def exists(self):
        return self.changesets or False
        
    def format(self):
        if not self.changesets:
            message = _("No changesets for #%s" % self.tkt_id)
            yield tag.span(format_to_oneliner(self.env, self.context, message, 
                                              shorten=False),
                           class_='ticketchangesets hint')
            return
        n = len(self.changesets)
        ix = 0 # current index for adding separation markers between repos
        for (reponame, changesets) in self.changesets:
            if n > 1:
                if self.hint == 'ticket':
                    if reponame and reponame != '(default)':
                        yield tag.h3(reponame, class_='change')
                    else:
                        yield tag.h3(_("Default Repository"), class_='change')
                elif ix > 0:
                    yield ', '
            revs = changesets.wiki_revs(reponame, self.compact)
            log = changesets.wiki_log(reponame)
            message = revs + ' (' + log + ')'
            yield tag.span(format_to_oneliner(self.env, self.context, message,
                                              shorten=False),
                           class_='ticketchangesets')
            ix += 1


class CommitMessageMacro(WikiMacroBase):
    """Insert a changeset message into the output.
    
    This macro must be called using wiki processor syntax as follows:
    {{{
    {{{
    #!CommitMessage repository="reponame" revision="rev"
    }}}
    }}}
    or
    {{{
    [[CommitMessage(repository, revision)]]
    }}}
    where the arguments are the following:
    - `repository`: the repository containing the changeset, 
                    default repository if omitted
    - `revision`: the revision of the desired changeset
    Arguments can be stated in any order.
    """
    
    def __init__(self):
        init_translation(self.env.path)
    
    def expand_macro(self, formatter, name, content, args={}):
        if args:
            reponame = args.get('repository', '')
            rev = args.get('revision')
        else:
            if ',' in content:
                reponame = ''
                rev = 0
                for c in [x.strip() for x in content.split(',')]:
                    if c.isnumeric():
                        rev = c
                    else:
                        reponame = c
            else:
                rev = content.strip()
                reponame = ''
        repos = RepositoryManager(self.env).get_repository(reponame)
        if repos:
            changeset = repos.get_changeset(rev)
            message = changeset.message
            rev = changeset.rev
        else:
            message = content
        if formatter.context.resource.realm == 'ticket':
            ticket_re = CommitTicketUpdater.ticket_re
            if not any(int(tkt_id) == formatter.context.resource.id
                       for tkt_id in ticket_re.findall(message)):
                return tag.div(tag.p(_("(The changeset message doesn't "
                    "reference this ticket)"), class_='hint'),
                    class_='commitmessage')
        if ChangesetModule(self.env).wiki_format_messages:
            return tag.div(format_to_html(self.env,
                formatter.context('changeset', rev, parent=repos.resource),
                message, escape_newlines=True), class_='commitmessage')
        else:
            return tag.pre(message, class_='commitmessage')
