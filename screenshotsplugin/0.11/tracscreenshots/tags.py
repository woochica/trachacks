# -*- coding: utf8 -*-

import sets

from trac.core import *
from trac.mimeview import Context
from trac.util.html import html
from trac.wiki.formatter import format_to_html, format_to_oneliner

from tractags.api import ITaggingSystemProvider, DefaultTaggingSystem, \
  TagEngine

from tracscreenshots.api import *

class ScreenshotsTaggingSystem(DefaultTaggingSystem):
    """
      Tagging system which returns tags of all created screenshots.
    """
    def __init__(self, env, req):
        # Create context object.
        self.context = Context.from_request(req)('screenshots-tags')

        DefaultTaggingSystem.__init__(self, env, 'screenshots')

    def name_details(self, name):
        # Get database access.
        db = self.env.get_db_cnx()
        self.context.cursor = db.cursor()

        # Get tagged screenshots.
        api = self.env[ScreenshotsApi]
        screenshot = api.get_screenshot(self.context, name)

        # Return a tuple of (href, wikilink, title)
        defaults = DefaultTaggingSystem.name_details(self, name)
        if screenshot:
            return (defaults[0], html.a(screenshot['name'], href =
              self.env.href.screenshots(screenshot['id']), title =
              screenshot['description']), screenshot['description'])
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
        return ScreenshotsTaggingSystem(self.env, None)

    # IScreenshotChangeListener methods.

    def screenshot_created(self, screenshot):
        # Add tags to screenshot.
        tags = TagEngine(self.env).tagspace.screenshots
        tag_names = self._get_tags(screenshot)
        tags.replace_tags(None, screenshot['id'], list(sets.Set(tag_names)))

    def screenshot_changed(self, screenshot, old_screenshot):
        # Add tags to screenshot.
        self.log.debug(screenshot['components'])
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
