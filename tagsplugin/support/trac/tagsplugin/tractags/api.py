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
tags.add_tag('WikiStart', 'start')
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

    def count_tagged_names(self, tagspace, tag = None):
        """ Count names in the given tagspace, optionally only those with the
            given tag. """
        raise NotImplementedError

    def get_tagged_names(self, tagspace, tag = None):
        """ Return an iterable over names in the given tagspace, optionally
            only those tagged with tag. """
        raise NotImplementedError

    def count_tags(self, tagspace, name = None):
        """ Count tags in the given tagspace, optionally only those tagging name. """
        raise NotImplementedError

    def get_tags(self, tagspace, name = None):
        """ Return an iterable over tags in tagspace, optionally only those
            tagging name.  """
        raise NotImplementedError

    def add_tag(self, tagspace, name, tag):
        """ Tag name in tagspace with tag. """
        raise NotImplementedError

    def remove_tag(self, tagspace, name, tag):
        """ Remove a tag from a name in a tagspace. """
        raise NotImplementedError

class TracTaggingSystem(TaggingSystem):
    """ Default tagging system. Handles any number of namespaces registered via
        ITagSpaceUser. """

    def _tags_cursor(self, action, tagspace, name, constraint):
        db = self.env.get_db_cnx()
        order = name == 'name' and 'tag' or 'name'
        opts = [tagspace]
        sql = "SELECT " + action + " FROM tags WHERE tagspace=%s"
        if constraint is not None:
            sql += " AND " + name + "=%s"
            opts.append(constraint)
        sql += " ORDER BY %s" % order 
        cursor = db.cursor()
        cursor.execute(sql, opts)
        return cursor

    def count_tags(self, tagspace, name = None):
        cursor = self._tags_cursor("COUNT(*)", tagspace, 'name', name)
        return cursor.fetchone()[0]

    def get_tags(self, tagspace, name = None):
        cursor = self._tags_cursor("tag", tagspace, 'name', name)
        for row in cursor:
            yield row[0]

    def count_tagged_names(self, tagspace, tag = None):
        cursor = self._tags_cursor("COUNT(*)", tagspace, 'tag', tag)
        return cursor.fetchone()[0]

    def get_tagged_names(self, tagspace, tag = None):
        cursor = self._tags_cursor("name", tagspace, 'tag', tag)
        for row in cursor:
            yield row[0]
        
    def add_tag(self, tagspace, name, tag):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('INSERT INTO tags (tagspace, name, tag) VALUES (%s, %s, %s)', (tagspace, name, tag))

    def remove_tag(self, tagspace, name, tag):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("DELETE FROM tags WHERE tagspace = %s AND name = %s AND tag = %s", (tagspace, name, tag))

# Simple class to proxy calls to TaggingSystem objects, automatically passing
# the tagspace argument to method calls.
class TaggingSystemAccessor(object):
    def __init__(self, tagspace, tagsystem):
        self.tagspace = tagspace
        self.tagsystem = tagsystem

    def __getattr__(self, name):
        return lambda *args, **kwargs: getattr(self.tagsystem, name)(self.tagspace, *args, **kwargs)

class TagEngine(Component):
    """ The core of the Trac tag API. This interface can be used to register
        tagspaces (ITagSpaceUser or register_tagspace()), add other tagging
        systems (ITaggingSystemProvider), and to control tags in a tagspace.
    """

    _tagspace_re = re.compile(r'''^[a-zA-Z_][a-zA-Z0-9_]*$''')

    implements(ITaggingSystemProvider, IEnvironmentSetupParticipant)

    tagusers = ExtensionPoint(ITagSpaceUser)
    taggingsystems = ExtensionPoint(ITaggingSystemProvider)

    SCHEMA = [
        Table('tags', key = ('tagspace', 'name', 'tag'))[
              Column('tagspace'),
              Column('name'),
              Column('tag'),
              Index(['tagspace', 'name']),
              Index(['tagspace', 'tag']),]
        ]

    def __init__(self):
        self.tagging_system = TracTaggingSystem(self.env)

    def _get_tagspaces(self):
        """ Get iterable of available tagspaces. """
        for tagsystem in self.taggingsystems:
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
        for tagsystem in self.taggingsystems:
            if tagspace in tagsystem.get_tagspaces_provided():
                return TaggingSystemAccessor(tagspace, tagsystem.get_tagging_system(tagspace))
        raise TracError("No such tagspace '%s'" % tagspace)
                
    # ITaggingSystemProvider methods
    def get_tagspaces_provided(self):
        for user in self.tagusers:
            for tagspace in user.tagspaces_used():
                yield tagspace

    def get_tagging_system(self, tagspace):
        for taguser in self.tagusers:
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

