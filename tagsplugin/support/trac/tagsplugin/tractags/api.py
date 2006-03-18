"""

Implementation of a generic tagging API for Trac. The API lets plugins register
use of a set of namespaces (tagspaces) then access and manipulate the tags in
that tagspace.

For integration of external programs, the API also allows other tag systems to
be accessed transparently (see the ITaggingSystemProvider interface and the
corresponding TaggingSystem class).

Taggable names are contained in a tagspace and can be associated with any
number of tags. eg. ('wiki', 'WikiStart', 'start') represents a 'start' tag to
the 'WikiStart' page in the 'wiki' tagspace.

For a component to register a new tagspace for use it must implement the
ITagSpaceUser interface.

To access tags for a tagspace use the following mechanism (using the 'wiki'
tagspace in this example):

{{{
#!python
from tractags.api import TagEngine

tags = TagEngine(env).wiki
# Display all names and the tags associated with each name
for name in tags.get_tagged_names():
    print name, list(tags.get_tags(name))
# Display all tags and the names associated with each tag
for tag in tags.get_tags():
    print tag, list(tags.get_tagged_names(tag))
# Add a start tag to WikiStart
tags.add_tag(req, 'WikiStart', 'start')
}}}

"""

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index, DatabaseManager
import sys
import re

class ITagSpaceUser(Interface):
    """ Register that this component uses a set of tagspaces. If a tagspace is
        not registered, it can not be used. """
    def tagspaces_used():
        """ Return an iterator of tagspaces used by this plugin. """

class ITaggingSystemProvider(Interface):
    """ An implementation of a tag system. This allows other non-Trac-native
        tag systems to be accessed through one API. """

    def get_tagspaces_provided():
        """ Iterable of tagspaces provided by this tag system. """

    def get_tagging_system(tagspace):
        """ Return the TaggingSystem responsible for tagspace. """

class TaggingSystem(object):
    """ An implementation of a tagging system. """
    def __init__(self, env):
        self.env = env

    def count_tagged_names(self, tagspace, *tags):
        """ Count tagged names in the given tagspace, optionally only those
            with the given tag. """
        return len(self.get_tagged_names(tagspace, *tags))

    def get_tagged_names(self, tagspace, *tags):
        """ Return a set() of tagged names in the given tagspace, optionally
            only those any of tags are applied to. """
        raise NotImplementedError

    def count_tags(self, tagspace, *names):
        """ Count tags in the given tagspace, optionally only those tagging name. """
        return len(self.get_tags(tagspace, *names))

    def get_tags(self, tagspace, *names):
        """ Return a set() of tags in tagspace, optionally the union of all
            tags on names. """
        raise NotImplementedError

    def add_tag(self, tagspace, req, name, tag):
        """ Tag name in tagspace with tag. """
        raise NotImplementedError

    def replace_tags(self, tagspace, req, name, *tags):
        """ Replace existing tags on name with tags. """
        self.remove_all_tags(tagspace, req, name)
        for tag in tags:
            self.add_tag(tagspace, req, name, tag)

    def remove_tag(self, tagspace, req, name, tag):
        """ Remove a tag from a name in a tagspace. """
        raise NotImplementedError

    def remove_all_tags(self, tagspace, req, name):
        """ Remove all tags from a named object. """
        for tag in self.get_tags(tagspace, name):
            self.remove_tag(tagspace, req, name, tag)

    def name_details(self, tagspace, name):
        """ Return a tuple of (href, htmllink, title). eg. 
            ("/ticket/1", "<a href="/ticket/1">#1</a>", "Broken links") """
        raise NotImplementedError

class DefaultTaggingSystem(TaggingSystem):
    """ Default tagging system. Handles any number of namespaces registered via
        ITagSpaceUser. """

    def _tags_cursor(self, action, tagspace, name, constraint):
        db = self.env.get_db_cnx()
        order = name == 'name' and 'tag' or 'name'
        opts = [tagspace]
        sql = "SELECT DISTINCT " + action + " FROM tags WHERE tagspace=%s"
        if constraint:
            sql += " AND " + name + " IN ('%s')" % "', '".join(constraint)
        sql += " ORDER BY %s" % order 
        cursor = db.cursor()
        cursor.execute(sql, opts)
        return cursor

    def count_tags(self, tagspace, *names):
        cursor = self._tags_cursor("COUNT(*)", tagspace, 'name', names)
        return cursor.fetchone()[0]

    def get_tags(self, tagspace, *names):
        cursor = self._tags_cursor("tag", tagspace, 'name', names)
        return set([row[0] for row in cursor])

    def count_tagged_names(self, tagspace, *tags):
        cursor = self._tags_cursor("COUNT(*)", tagspace, 'tag', tags)
        return cursor.fetchone()[0]

    def get_tagged_names(self, tagspace, *tags):
        cursor = self._tags_cursor("name", tagspace, 'tag', tags)
        return set([row[0] for row in cursor])
        
    def add_tag(self, tagspace, req, name, tag):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO tags (tagspace, name, tag) VALUES (%s, %s, %s)', (tagspace, name, tag))
        db.commit()

    def remove_tag(self, tagspace, req, name, tag):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM tags WHERE tagspace = %s AND name = %s AND tag = %s", (tagspace, name, tag))
        db.commit()

    def remove_all_tags(self, tagspace, req, name):
        """ Remove all tags from a named object. """
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM tags WHERE tagspace = %s AND name = %s", (tagspace, name))
        db.commit()

    def name_details(self, tagspace, name):
        from trac.wiki.formatter import wiki_to_oneliner
        return (getattr(self.env.href, tagspace),
                wiki_to_oneliner('[%s:%s %s]' % (tagspace, name, name),
                                  self.env), '')

# Simple class to proxy calls to TaggingSystem objects, automatically passing
# the tagspace argument to method calls.
class TaggingSystemAccessor(object):
    def __init__(self, tagspace, tagsystem):
        self.tagspace = tagspace
        self.tagsystem = tagsystem

    def __getattr__(self, name):
        def accessor(*args, **kwds):
            return getattr(self.tagsystem, name)(self.tagspace, *args, **kwds)
        return accessor

    def __repr__(self):
        return repr(self.tagsystem)

class TagEngine(Component):
    """ The core of the Trac tag API. This interface can be used to register
        tagspaces (ITagSpaceUser or register_tagspace()), add other tagging
        systems (ITaggingSystemProvider), and to control tags in a tagspace.
    """

    _tagspace_re = re.compile(r'''^[a-zA-Z_][a-zA-Z0-9_]*$''')

    implements(ITaggingSystemProvider, IEnvironmentSetupParticipant)

    tag_users = ExtensionPoint(ITagSpaceUser)
    tagging_systems = ExtensionPoint(ITaggingSystemProvider)

    SCHEMA = [
        Table('tags', key = ('tagspace', 'name', 'tag'))[
              Column('tagspace'),
              Column('name'),
              Column('tag'),
              Index(['tagspace', 'name']),
              Index(['tagspace', 'tag']),]
        ]

    def __init__(self):
        self.tagging_system = DefaultTaggingSystem(self.env)

    def _get_tagspaces(self):
        """ Get iterable of available tagspaces. """
        for tagsystem in self.tagging_systems:
            for tagspace in tagsystem.get_tagspaces_provided():
                yield tagspace
    tagspaces = property(_get_tagspaces)

    def __getattr__(self, tagspace):
        """ Convenience method for accessing TaggingSystems. eg. to access the
            'wiki' tagspace, use TagEngine(env).wiki """
        return self.get_tagsystem(tagspace)

    def get_tagsystem(self, tagspace):
        """ Returns a TaggingSystem proxy object with tagspace as the default
            tagspace. """
        for tagsystem in self.tagging_systems:
            if tagspace in tagsystem.get_tagspaces_provided():
                return TaggingSystemAccessor(tagspace,
                       tagsystem.get_tagging_system(tagspace))
        raise TracError("No such tagspace '%s'" % tagspace)

    def get_tag_link(self, tag):
        """ Return (href, title) to information about tag. This first checks for
            a Wiki page named <tag>, then uses /tags/<tag>. """
        from tractags.wiki import WikiTaggingSystem
        page, title = WikiTaggingSystem(self.env).page_info(tag)
        if page.exists:
            return (self.env.href.wiki(tag), title)
        else:
            return (self.env.href.tags(tag), "Objects tagged ''%s''" % tag)

    def get_tags(self, *names):
        """ Get all tags from all namespaces. """
        tags = set()
        for tagsystem in self.tagging_systems:
            for tagspace in tagsystem.get_tagspaces_provided():
                tags.update(tagsystem.get_tags(tagspace, *names))
        return tags

    def count_tags(self, *names):
        return len(self.get_tags(*names))

    def get_tagged_names(self, *tags):
        """ Get all tagged names from all namespaces. Returns a dictionary with
            the tagspace as the key and the value a list of names in that
            tagspace. """
        names = {}
        for tagsystem in self.tagging_systems:
            for tagspace in tagsystem.get_tagspaces_provided():
                names[tagspace] = tagsystem.get_tagged_names(tagspace, *tags)
        return names

    def count_tagged_names(self, *tags):
        return len(get_tagged_names(*tags))

    # ITaggingSystemProvider methods
    def get_tagspaces_provided(self):
        for user in self.tag_users:
            for tagspace in user.tagspaces_used():
                yield tagspace

    def get_tagging_system(self, tagspace):
        for taguser in self.tag_users:
            if tagspace in taguser.tagspaces_used():
                return self.tagging_system
        raise TracError("No such tagspace '%s'" % tagspace)

    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        self._upgrade_db(self.env.get_db_cnx())

    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        if self._need_migration(db):
            return True
        try:
            cursor.execute("select count(*) from tags")
            cursor.fetchone()
            return False
        except:
            return True

    def upgrade_environment(self, db):
        self._upgrade_db(db)

    def _need_migration(self, db):
        cursor = db.cursor()
        try:
            cursor.execute("select count(*) from wiki_namespace")
            cursor.fetchone()
            self.env.log.debug("tractags needs to migrate old data")
            return True
        except:
            return False

    def _upgrade_db(self, db):
        try:
            db_backend, _ = DatabaseManager(self.env)._get_connector()

            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)

            # Migrate old data
            if self._need_migration(db):
                cursor.execute("INSERT INTO tags (tagspace, name, tag) SELECT 'wiki', name, namespace FROM wiki_namespace")
                cursor.execute("DROP TABLE wiki_namespace")
        except Exception, e:
            db.rollback()
            raise TracError(str(e))

        db.commit()

