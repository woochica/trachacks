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

tags = TagEngine(env).tagspace.wiki
# Display all names and the tags associated with each name
for name in tags.get_tagged_names():
    print name, list(tags.get_name_tags(name))
# Display all tags and the names associated with each tag
for tag in tags.get_tags():
    print tag, list(tags.get_tagged_names(tag))
# Add a start tag to WikiStart
tags.add_tags(None, 'WikiStart', ['start'])
}}}

"""

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.db import Table, Column, Index
import sys
import re

try:
    set = set
except:
    from sets import Set as set

try:
    sorted = sorted
except NameError:
    def sorted(iterable):
        lst = list(iterable)
        lst.sort()
        return lst

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
    def __init__(self, env, tagspace):
        self.env = env
        self.tagspace = tagspace

    def walk_tagged_names(self, names, tags, predicate):
        """ Generator returning a tuple of (name, tags) for each tagged name
            in this tagspace that meets the predicate and is in the set
            of names and has any of the given tags.

            predicate is called with (name, tags)

            (The names and tags arguments are purely an optimisation
            opportunity for the underlying TaggingSystem)
            """

    def get_name_tags(self, name):
        """ Get tags for a name. """
        raise NotImplementedError

    def add_tags(self, req, name, tags):
        """ Tag name in tagspace with tags. """
        raise NotImplementedError

    def replace_tags(self, req, name, tags):
        """ Replace existing tags on name with tags. """
        self.remove_all_tags(req, name)
        self.add_tags(req, name, tags)

    def remove_tags(self, req, name, tags):
        """ Remove tags from a name in a tagspace. """
        raise NotImplementedError

    def remove_all_tags(self, req, name):
        """ Remove all tags from a name in a tagspace. """
        self.remove_tags(req, name, self.get_name_tags(name))

    def name_details(self, name):
        """ Return a tuple of (href, htmllink, title). eg. 
            ("/ticket/1", "<a href="/ticket/1">#1</a>", "Broken links") """
        raise NotImplementedError

class DefaultTaggingSystem(TaggingSystem):
    """ Default tagging system. Handles any number of namespaces registered via
        ITagSpaceUser. """

    def walk_tagged_names(self, names, tags, predicate):
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        args = [self.tagspace]
        sql = 'SELECT DISTINCT name, tag FROM tags WHERE tagspace=%s'
        if names:
            sql += ' AND name IN (' + ', '.join(['%s' for n in names]) + ')'
            args += names
        if tags:
            sql += ' AND name in (SELECT name FROM tags WHERE tag in (' + ', '.join(['%s' for t in tags]) + '))'
            args += tags
        sql += " ORDER BY name"
        cursor.execute(sql, args)

        tags = set(tags)
        current_name = None
        name_tags = set()
        for name, tag in cursor:
            if current_name != name:
                if current_name is not None:
                    if predicate(current_name, name_tags):
                        yield (current_name, name_tags)
                name_tags = set([tag])
                current_name = name
            else:
                name_tags.add(tag)
        if current_name is not None and predicate(current_name, name_tags):
            yield (current_name, name_tags)

    def get_name_tags(self, name):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('SELECT tag FROM tags WHERE tagspace=%s AND name=%s', (self.tagspace, name))
        return set([row[0] for row in cursor])

    def add_tags(self, req, name, tags):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        for tag in tags:
            cursor.execute('INSERT INTO tags (tagspace, name, tag) VALUES (%s, %s, %s)', (self.tagspace, name, tag))
        db.commit()

    def remove_tags(self, req, name, tags):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        sql = "DELETE FROM tags WHERE tagspace = %s AND name = %s AND tag " \
              "IN (" + ', '.join(["%s" for t in tags]) + ")"
        cursor.execute(sql, (self.tagspace, name) + tuple(tags))
        db.commit()

    def remove_all_tags(self, req, name):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute('DELETE FROM tags WHERE tagspace=%s AND name=%s', (self.tagspace, name))
        db.commit()
        
    def name_details(self, name):
        from trac.wiki.formatter import wiki_to_oneliner
        return (getattr(self.env.href, self.tagspace),
                wiki_to_oneliner('[%s:"%s" %s]' % (self.tagspace, name, name), self.env), '')

class TagspaceProxy:
    """ A convenience for performing operations on a specific tagspace,
        including get_tags() and get_tagged_names(). Both of these functions
        will only search that tagspace, and will return values stripped of
        tagspace information. """
    def __init__(self, engine, tagspace):
        self.engine = engine
        self.tagspace = tagspace
        self.tagsystem = engine._get_tagsystem(tagspace)

    def get_tags(self, *args, **kwargs):
        result = self.engine.get_tags(tagspaces=[self.tagspace], *args, **kwargs)
        if isinstance(result, set):
            return result
        else:
            out = {}
            for tag, names in result.iteritems():
                out[tag] = set([name for _, name in names])
            return out

    def get_tagged_names(self, *args, **kwargs):
        return self.engine.get_tagged_names(tagspaces=[self.tagspace], *args, **kwargs)[self.tagspace]

    def __getattr__(self, attr):
        return getattr(self.tagsystem, attr)

class TagspaceDirector(object):
    """ A convenience similar to env.href, proxying to the correct TagSystem by
        attribute. """
    def __init__(self, engine):
        self.engine = engine

    def __getattr__(self, tagspace):
        return self.tagspace(tagspace)

    def tagspace(self, tagspace):
        return TagspaceProxy(self.engine, tagspace)

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
        self.tagspace = TagspaceDirector(self)
        self._tagsystem_cache = {}
        self._tag_link_cache = {}

    def _get_tagspaces(self):
        """ Get iterable of available tagspaces. """
        out = []
        for tagsystem in self.tagging_systems:
            for tagspace in tagsystem.get_tagspaces_provided():
                out.append(tagspace)
        return out
    tagspaces = property(_get_tagspaces)

    def _get_tagsystem(self, tagspace):
        """ Returns a TaggingSystem proxy object with tagspace as the default
            tagspace. """
        try:
            return self._tagsystem_cache[tagspace]
        except KeyError:
            for tagsystem in self.tagging_systems:
                if tagspace in tagsystem.get_tagspaces_provided():
                   self._tagsystem_cache[tagspace] = tagsystem.get_tagging_system(tagspace)
                   return self._tagsystem_cache[tagspace]
        raise TracError("No such tagspace '%s'" % tagspace)

    # Public methods
    def flush_link_cache(self, tag=None):
        """ Flush the link cache entirely, or for a single tag. """
        if not tag:
            self._tag_link_cache = {}
        elif tag in self._tag_link_cache:
            del self._tag_link_cache[tag]

    def walk_tagged_names(self, names=[], tags=[], tagspaces=[], predicate=lambda tagspace, name, tags: True):
        """ Generator returning (tagspace, name, tags) for all names in the
            given tagspaces. Objects must have at least one of tags, be in
            names and must meet the predicate. """
        tagspaces = tagspaces or self.tagspaces
        for tagspace in tagspaces:
            tagsystem = self._get_tagsystem(tagspace)
            for name, name_tags in tagsystem.walk_tagged_names(names=names, tags=tags, predicate=lambda n, t: predicate(tagspace, n, t)):
                yield (tagspace, name, name_tags)

    def get_tags(self, names=[], tagspaces=[], operation='union', detailed=False):
        """ Get tags with the given names from the given tagspaces.
            'operation' is the union or intersection of all tags on
            names. If detailed, return a set of
            {tag:set([(tagspace, name), ...])}, otherwise return a set of
            tags. """
        assert type(names) in (list, tuple, set)
        tagspaces = tagspaces or self.tagspaces
        seed_set = True
        all_tags = set()
        tagged_names = {}
        for tagspace, name, tags in self.walk_tagged_names(names=names, tagspaces=tagspaces):
            for tag in tags:
                tagged_names.setdefault(tag, set()).add((tagspace, name))
            if operation == 'intersection':
                if seed_set:
                    seed_set = False
                    all_tags.update(tags)
                else:
                    all_tags.intersection_update(tags)
                    if not all_tags:
                        return detailed and {} or set()
            else:
                all_tags.update(tags)
        if detailed:
            out_tags = {}
            for tag in all_tags:
                out_tags[tag] = tagged_names[tag]
            return out_tags
        else:
            return all_tags

    def get_tagged_names(self, tags=[], tagspaces=[], operation='intersection', detailed=False):
        """ Get names with the given tags from tagspaces. 'operation' is the set
            operatin to perform on the sets of names tagged with each of the
            search tags, and can be either 'intersection' or 'union'.

            If detailed=True return a dictionary of
            {tagspace:{name:set([tag, ...])}} otherwise return a dictionary of
            {tagspace:set([name, ...])}. """
        assert type(tags) in (list, tuple, set)
        tagspaces = tagspaces or self.tagspaces
        tags = set(tags)
        if detailed:
            output = dict([(ts, {}) for ts in tagspaces])
        else:
            output = dict([(ts, set()) for ts in tagspaces])
        for tagspace, name, name_tags in self.walk_tagged_names(tags=tags, tagspaces=tagspaces):
            if operation == 'intersection' and tags.intersection(name_tags) != tags:
                continue
            if detailed:
                output[tagspace][name] = name_tags
            else:
                output[tagspace].add(name)
        return output

    def get_tag_link(self, tag):
        """ Return (href, title) to information about tag. This first checks for
            a Wiki page named <tag>, then uses /tags/<tag>. """
        if tag in self._tag_link_cache:
            return self._tag_link_cache[tag]
        from tractags.wiki import WikiTaggingSystem
        page, title = WikiTaggingSystem(self.env).page_info(tag)
        if page.exists:
            result = (self.env.href.wiki(tag), title)
        else:
            result = (self.env.href.tags(tag), "Objects tagged ''%s''" % tag)
        self._tag_link_cache[tag] = result
        return result
    

    def name_details(self, tagspace, name):
        """ Return a tuple of (href, htmllink, title). eg. 
            ("/ticket/1", "<a href="/ticket/1">#1</a>", "Broken links") """
        return self._get_tagsystem(tagspace).name_details(name)

    # ITaggingSystemProvider methods
    def get_tagspaces_provided(self):
        for user in self.tag_users:
            for tagspace in user.tagspaces_used():
                yield tagspace

    def get_tagging_system(self, tagspace):
        for taguser in self.tag_users:
            if tagspace in taguser.tagspaces_used():
                return DefaultTaggingSystem(self.env, tagspace)
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
            db.rollback()
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
            db.rollback()
            return False

    def _upgrade_db(self, db):
        try:
            try:
                from trac.db import DatabaseManager
                db_backend, _ = DatabaseManager(self.env)._get_connector()
            except ImportError:
                db_backend = self.env.get_db_cnx()

            cursor = db.cursor()
            for table in self.SCHEMA:
                for stmt in db_backend.to_sql(table):
                    self.env.log.debug(stmt)
                    cursor.execute(stmt)
            db.commit()

            # Migrate old data
            if self._need_migration(db):
                cursor = db.cursor()
                cursor.execute("INSERT INTO tags (tagspace, name, tag) SELECT 'wiki', name, namespace FROM wiki_namespace")
                cursor.execute("DROP TABLE wiki_namespace")
                db.commit()
        except Exception, e:
            db.rollback()
            self.env.log.error(e, exc_info=1)
            raise TracError(str(e))
