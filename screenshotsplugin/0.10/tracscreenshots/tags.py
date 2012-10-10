# -*- coding: utf-8 -*-

import sets

from tracscreenshots.api import *
from trac.core import *

from tractags.api import ITaggingSystemProvider, DefaultTaggingSystem, \
  TagEngine

class ScreenshotsTaggingSystem(DefaultTaggingSystem):
    """
      Tagging system which returns tags of all created screenshots.
    """
    def __init__(self, env, component, req):
        self.component = component
        self.req = req
        DefaultTaggingSystem.__init__(self, env, 'screenshots')

    def name_details(self, name):
        # Get cursor.
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        # Get tagged screenshots.
        api = self.env[ScreenshotsApi]
        screenshot = api.get_screenshot(cursor, name)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        if screenshot:
            return (defaults[0], wiki_to_oneliner('[screenshot:%s %s]' %
              (screenshot['id'], screenshot['name']), self.env),
              screenshot['description'])
        else:
            return defaults

class ScreenshotsTags(Component):
    """
        The tags module implements plugin's ability to create tags related
        to screenshots.
    """
    implements(ITaggingSystemProvider, IScreenshotChangeListener)

    # ITaggingSystemProvider methods.

    def get_tagspaces_provided(self):
        yield 'screenshots'

    def get_tagging_system(self, tagspace):
        return ScreenshotsTaggingSystem(self.env, self, None)

    # IScreenshotChangeListener methods.

    def screenshot_created(self, screenshot):
        # Add tags to screenshot.
        tags = TagEngine(self.env).tagspace.screenshots
        tag_names = self._get_tags(screenshot)
        tags.replace_tags(None, screenshot['id'], list(sets.Set(tag_names)))

    def screenshot_changed(self, screenshot, old_screenshot):
        # Add tags to screenshot.
        old_screenshot.update(screenshot)
        tags = TagEngine(self.env).tagspace.screenshots
        tag_names = self._get_tags(old_screenshot)
        tags.replace_tags(None, old_screenshot['id'], list(sets.Set(tag_names)))

    def screenshot_deleted(self, screenshot):
        # Add tags to screenshot.
        tags = TagEngine(self.env).tagspace.screenshots
        tag_names = self._get_tags(screenshot)
        tags.remove_tags(None, screenshot['id'], list(sets.Set(tag_names)))

    def _get_tags(self, screenshot):
        # Prepare tag names.
        tags = [screenshot['author']]
        if screenshot['components']:
            tags += [component for component in screenshot['components']]
        if screenshot['versions']:
            tags += [version for version in screenshot['versions']]
        if screenshot['name']:
            tags += [screenshot['name']]
        if screenshot['tags']:
            tags += screenshot['tags'].split()
        self.log.debug(tags)
        return tags
