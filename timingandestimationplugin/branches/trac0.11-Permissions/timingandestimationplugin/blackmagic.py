from trac.core import Component, implements, TracError
from trac.config import Option, IntOption, ListOption, BoolOption
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from pkg_resources import resource_filename
from trac.web.api import ITemplateStreamFilter
from genshi.builder import tag
from genshi.core import Markup, Stream
from genshi.filters.transform import Transformer
import re, cPickle
from trac.perm import IPermissionRequestor

#@staticmethod
def disable_field(stream, field):
    def helper(field_stream):
        value = Stream(field_stream).select('@value').render()
        for kind,data,pos in tag.span(value, id=("field-%s"%field)).generate():
            yield kind,data,pos

    return stream | Transformer(
        '//input[@id="field-%s"]' % field
        ).filter(helper)


def remove_header(stream, field):
    """ Removes the display from the ticket properties """
    stream = stream | Transformer('//th[@id="h_%s"]' % field).replace(tag.th(id="h_%s" % field))
    stream = stream | Transformer('//td[@headers="h_%s"]' % field).replace(tag.th(id="h_%s" % field))
    return stream

def remove_field(stream , field):
    """ Removes a field from the form area"""
    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(" ")
    stream = stream | Transformer('//*[@id="field-%s"]' % field).replace(" ")
    return remove_header(stream , field)


def istrue(v, otherwise=None):
    if v.lower() in ('yes', 'true', '1', 'on'):
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
        if not filename == "ticket.html":
            return stream
        enchants = self.config.getlist('field settings', 'fields', '')
        for field in enchants:
            self.log.debug('BlackMagicing: %s' % field)
            disabled = False
            hidden = False
            hide_summary = False
            perms = self.config.getlist('field settings', '%s.permission' % field, [])
            self.log.debug('BlackMagicing - read permission config: %s has %s' % (field, perms))
            for (perm, denial) in [s.split(":") for s in perms] :
                perm = perm.upper()
                self.log.debug('BlackMagicing - testing permission: %s has %s = %s' % (field, perm, (perm not in req.perm or perm == "ALWAYS")))
                if (perm not in req.perm or perm == "ALWAYS"): 
                    if denial:
                        denial = denial.lower()
                        if denial == "disable":
                            disabled = True
                        elif denial == "hide":
                            hidden = True
                        else:
                            disabled = True
                    else:
                        disabled = True
                    
                if disabled or istrue(self.config.get('field settings', '%s.disable' % field, False)):
                    self.log.debug('BlackMagic disabling: %s' % field)
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).attr("disabled", "disabled")
                    if not self.gray_disabled:
                        stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                            tag.strike()('%s:' % field.capitalize())
                        )
                    else:
                        stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                            tag.span(style="color:%s" % self.gray_disabled)('%s:' % field.capitalize())
                        )

                if self.config.get('field settings', '%s.label' % field, None):
                    self.log.debug('BlackMagic labeling: %s' % field)
                    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                        self.config.get('field settings', '%s.label' % field)
                    )
                    
                if self.config.get('field settings', '%s.notice' % field, None):
                    self.log.debug('BlackMagic noticing: %s' % field)
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).after(
                        tag.br() + tag.small()(
                            tag.em()(
                                Markup(self.config.get('field settings', '%s.notice' % field))
                            )
                        )
                    )
                    
                tip = self.config.get('field settings', '%s.tip' % field, None)
                if tip:
                    self.log.debug('BlackMagic tipping: %s' % field)
                    stream = stream | Transformer('//div[@id="banner"]').before(
                        tag.script(type="text/javascript", 
                        src=req.href.chrome("blackmagic", "js", "wz_tooltip.js"))()
                    )
                    
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).attr(
                        "onmouseover", "Tip('%s')" % tip.replace(r"'", r"\'")
                    )
                    
                if hidden or istrue(self.config.get('field settings', '%s.hide' % field, None)):
                    self.log.debug('BlackMagic hiding: %s' % field)
                    stream = remove_field(field)
                    
        return stream

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blackmagic', resource_filename(__name__, 'htdocs'))]
          
    def get_templates_dirs(self):
        return []    
