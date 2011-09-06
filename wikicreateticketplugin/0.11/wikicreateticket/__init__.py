import re
from trac.core import *
from trac.wiki import IWikiChangeListener, WikiPage
from trac.ticket import Ticket

class WikiCreateTicket(Component):
    """create ticket from wiki."""

    implements(IWikiChangeListener)

    _new_ticket_tag = '#new '
    _new_ticket_re = re.compile(r'#new (.*)$')

    def match_request(self, req):
        return 'WIKI_MODIFY' in req.perm and 'TICKET_CREATE' in req.perm

    def wiki_page_added(self, page):
        self.__parse_wiki_and_create_ticket(page, 1)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self.__parse_wiki_and_create_ticket(page, version)

    def wiki_page_deleted(self, page):
        pass

    def wiki_page_version_deleted(self, page):
        pass

    def __parse_wiki_and_create_ticket(self, page, version):
        page = WikiPage(self.env, page.name, version)

        lines = page.text.splitlines()
        new_lines = []

        for line in page.text.splitlines():
            matched = self._new_ticket_re.search(line)
            if matched:
                ticket_id = self.__create_new_ticket(page, matched.group(1), page.author)
                if ticket_id:
                    self.env.log.debug("create ticket from wiki: %s, ticket: %s" % (page.name, ticket_id))
                    new_line = line.replace(self._new_ticket_tag, '#%s ' % ticket_id, 1)
                else:
                    self.env.log.error("failed to create ticket from wiki: %s" % page.name)
                    new_line = line

            else:
                new_line = line

            new_lines.append(new_line)

        page.text = "\n".join(new_lines)
        self.__update_wiki(page)

    def __update_wiki(self, page):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        page.save
        cursor.execute("UPDATE wiki SET text=%s WHERE name=%s AND version=%s",
                    (page.text, page.name, page.version))
        db.commit()

    def __create_new_ticket(self, page, title, owner):
        matched = re.compile(r'^\[(.*)\](.*)').search(title)
        if matched:
            summary = matched.group(2)
            owner = matched.group(1)
        else:
            summary = title
            owner = None

        ticket = Ticket(self.env)
        ticket.values = {
            'status': 'new',
            'reporter': page.author,
            'summary': summary,
            'owner': owner,
            'description': "wiki:%s" % page.name,
        }
        return ticket.insert()
