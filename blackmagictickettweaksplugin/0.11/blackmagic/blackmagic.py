from trac.core import Component, implements, TracError
from trac.config import Option, IntOption, ListOption, BoolOption
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from pkg_resources import resource_filename
from trac.web.api import ITemplateStreamFilter
from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer
import re, cPickle
from trac.perm import IPermissionRequestor

def istrue(v, otherwise=None):
    if str(v).lower() in ('yes', 'true', '1', 'on'):
        return True
    else:
        if otherwise is None:
            return False
        else:
            return otherwise

class TicketTweaks(Component):
    implements(ITemplateStreamFilter, ITemplateProvider, IPermissionRequestor)

    permissions = ListOption('blackmagic', 'permissions', [])
    gray_disabled = Option('blackmagic', 'gray_disabled', '',
        doc="""If not set, disabled items will have their label striked through.
        Otherwise, this color will be used to gray them out. Suggested #cccccc.""")
    ## IPermissionRequestor methods

    def get_permission_actions(self):
        return (x.upper() for x in self.permissions)

    ## ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename == "ticket.html":
            enchants = self.config.get('blackmagic', 'tweaks', '')
            for field in (x.strip() for x in enchants.split(',')):

                disabled = False
                hidden = False
                perm = self.config.get('blackmagic', '%s.permission' % field, '').upper()
                if perm and perm not in req.perm:
                    denial = self.config.get('blackmagic', '%s.ondenial' % field, None)
                    if denial:
                        if denial == "disable":
                            disabled = True
                        elif denial == "hide":
                            hidden = True
                        else:
                            disabled = True
                    else:
                        disabled = True

                if disabled or istrue(self.config.get('blackmagic', '%s.disable' % field, False)):
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).attr("disabled", "disabled")
                    if not self.gray_disabled:
                        stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                            tag.strike()('%s:' % field.capitalize())
                        )
                    else:
                        stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                            tag.span(style="color:%s" % self.gray_disabled)('%s:' % field.capitalize())
                        )

                if self.config.get('blackmagic', '%s.label' % field, None):
                    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                        self.config.get('blackmagic', '%s.label' % field)
                    )

                if self.config.get('blackmagic', '%s.notice' % field, None):
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).after(
                        tag.br() + tag.small()(
                            tag.em()(
                                Markup(self.config.get('blackmagic', '%s.notice' % field))
                            )
                        )
                    )

                tip = self.config.get('blackmagic', '%s.tip' % field, None)
                if tip:
                    stream = stream | Transformer('//div[@id="banner"]').before(
                        tag.script(type="text/javascript",
                        src=req.href.chrome("blackmagic", "js", "wz_tooltip.js"))()
                    )

                    stream = stream | Transformer('//*[@id="field-%s"]' % field).attr(
                        "onmouseover", "Tip('%s')" % tip.replace(r"'", r"\'")
                    )

                if hidden or istrue(self.config.get('blackmagic', '%s.hide' % field, None)):
                    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(" ")
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).replace(" ")

        return stream

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blackmagic', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
