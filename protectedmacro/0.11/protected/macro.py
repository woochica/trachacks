import re

from genshi.builder import tag
from trac.attachment import Attachment
from trac.core import *
from trac.perm import IPermissionRequestor, IPermissionPolicy
from trac.web.api import IRequestFilter
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage

LEVELS = {"protected":{"action":"PROTECTED_VIEW", "style":"border-left:2px solid red; padding-left:3px"},
          "protected-red":{"action":"PROTECTED_RED_VIEW", "style":"border-left:2px solid red; padding-left:3px"},
          "protected-blue":{"action":"PROTECTED_BLUE_VIEW", "style":"border-left:2px solid blue; padding-left:3px"},
          "protected-green":{"action":"PROTECTED_GREEN_VIEW", "style":"border-left:2px solid green; padding-left:3px"}}

# def LOG(*args):
#    """Output debug information"""
#    f = open("/tmp/trac-temp", "a+")
#    for arg in args:
#        f.write(str(arg))
#        f.write("\n\n")
#    f.close()

class ProtectedAttachmentPolicy(Component):
    """
    Apply a permission check to attachments.

    Attachments are protected when the key-string "!protected",
    "!protected-red", "!protected-blue", or "!protected-green" is
    present in the attachment's description.
    
    When several "!protected-..." key-strings are used they are all
    evaluated. If all pass the attachment can be accessed.

    To enable the attachment protection the conf/trac.ini must be
    modified. Add the ProtectedAttachmentPolicy to the
    permission_policies:
    [trac]
    permission_policies = ProtectedAttachmentPolicy, DefaultPermissionPolicy    
    """
    implements(IPermissionPolicy)
    
    # IPermissionPolicy
    def check_permission(self, action, username, resource, perm):
        if action in ("ATTACHMENT_VIEW", "ATTACHMENT_DELETE"):
            attachment = Attachment(self.env, resource)

            result = True
            for name, level in LEVELS.iteritems():
                if "!%s" % name in attachment.description:
                    if not level["action"] in perm:
                        result = False

            return result

class ProtectedMacro(Component):
    """
    Apply a permission check to (parts of) a wiki page.

    A protected part has the following syntax:
    {{{
    #!protected
    #:This is what an unauthorized user sees (optional)
    This is what an authorized user sees
    }}}

    A protected part can use !protected, !protected-red,
    !protected-blue, or !protected-green to provide access
    restrictions on different levels. Users will only see these
    protected sections when they have the permissions
    "PROTECTED_VIEW", "PROTECTED_RED_VIEW", "PROTECTED_BLUE_VIEW", or
    "PROTECTED_GREEN_VIEW", respectively.
    """
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
    
class ProtectedFilter(Component):
    implements(IRequestFilter)

    # IRequestFilter
    def pre_process_request(self, req, handler):
        action = req.args.get("action", "view")

        if not action == "view":
            # this security filter applies to all non-VIEW
            # actions. Other actions, such as DELETE, EDIT, and DIFF
            # either give access to the protected parts, or allow
            # modification (removal in case of DELETE) of those parts
            
            pagename = req.args.get("page", "WikiStart")
            page = WikiPage(self.env, pagename)

            if pagename.endswith("/"):
                req.redirect(req.href.wiki(pagename.strip("/")))

            for name, level in LEVELS.iteritems():
                if re.search("^\s*#!%s\s*$" % name, page.text, re.MULTILINE):
                    # this page contains a ^#!protected$
                    # pattern. therefore: require the PROTECTED
                    # permission
                    req.perm(page.resource).require(level["action"])

        return handler

    # IRequestFilter
    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    # IRequestFilter
    def post_process_request(self, req, template, data, content_type):
        return (template, data, content_type)
