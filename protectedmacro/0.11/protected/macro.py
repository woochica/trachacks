from genshi.builder import tag
from trac.core import *
from trac.perm import IPermissionRequestor
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html

LEVELS = {"protected":{"action":"PROTECTED_VIEW", "style":"border-left:2px solid red; padding-left:3px"},
          "protected-red":{"action":"PROTECTED_RED_VIEW", "style":"border-left:2px solid red; padding-left:3px"},
          "protected-blue":{"action":"PROTECTED_BLUE_VIEW", "style":"border-left:2px solid blue; padding-left:3px"},
          "protected-green":{"action":"PROTECTED_GREEN_VIEW", "style":"border-left:2px solid green; padding-left:3px"}}

class ProtectedMacro(Component):
    implements(IPermissionRequestor, IWikiMacroProvider)

    # IWikiMacroProvider
    def get_macros(self):
        """Return an iterable that provides the names of the provided macros."""
        return LEVELS.keys()

    # IWikiMacroProvider
    def get_macro_description(self, name):
        return "A Trac macro to limit access to parts of a trac page."

    # IWikiMacroProvider
    def expand_macro(self, formatter, name, content):
        """Called by the formatter when rendering the parsed wiki text."""
        if name in LEVELS:
            level = LEVELS[name]

            if level["action"] in formatter.req.perm:
                # authorized
                content = "\n".join((line for line in content.split("\n") if not line.startswith("#:")))
            else:
                # unauthorized
                content = "\n".join((line[2:] for line in content.split("\n") if line.startswith("#:")))

            if content:
                return tag.div(format_to_html(self.env, formatter.context, content), style=level["style"])
            else:
                return ""

    # IPermissionRequestor,
    def get_permission_actions(self):
        return [level["action"] for level in LEVELS.values()]
    
