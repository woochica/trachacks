from tracscreenshots.api import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider

class ScreenshotsWiki(Component):
    """
        The wiki module implements macro for screenshots referencing.
    """
    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider
    def get_link_resolvers(self):
        yield ('screenshot', self._screenshot_link)

    def get_wiki_syntax(self):
        return []

    # Internal functions

    def _screenshot_link(self, formatter, ns, params, label):
        if ns == 'screenshot':
            # Get referenced screenshot.
            api = ScreenshotsApi(self)
            screenshot = api.get_screenshot(params)

            # Return macro content
            if screenshot:
                components = api.get_components()
                component = self._get_component_by_name(components,
                  screenshot['component'])
                versions =  api.get_versions()
                version = self._get_version_by_name(versions,
                  screenshot['version'])
                return '<a href="%s?component=%s;version=%s;id=%s" title="%s">' \
                  '%s</a>' % (self.env.href.screenshots(), component['id'],
                  version['id'], screenshot['id'], screenshot['name'], label)
            else:
                return '<a href="%s" class="missing">%s?</a>' % (
                  self.env.href.screenshots(), label)

    def _get_component_by_name(self, components, name):
        for component in components:
            if component['name'] == name:
                return component

    def _get_version_by_name(self, versions, name):
        for version in versions:
            if version['name'] == name:
                return version
