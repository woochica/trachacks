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

def textOf(self, **keys):
    return self.render('text', None, **keys)

Stream.textOf = textOf

#@staticmethod
def disable_field(stream, field):
    def select_helper(stream):
        s = Stream(stream)
        name = s.select('@name').textOf()
        opt = s.select('//option[@selected]')
        if not opt: s.select('//option[position()=1]')
        text = opt.select("text()").textOf()
        value = s.select('@value').textOf()
        if not value: value = text

        for kind,data,pos in tag.span(text, id=("field-%s"%field)).generate():
            yield kind,data,pos
        for kind,data,pos in tag.input(value=value, name=name, type="hidden").generate():
            yield kind,data,pos


    def helper(field_stream):
        s = Stream(field_stream)
        value = s.select('@value').textOf()
        name = s.select('@name').textOf()
        for kind,data,pos in tag.span(value, id=("field-%s"%field)).generate():
            yield kind,data,pos
        for kind,data,pos in tag.input(value=value, name=name, type="hidden").generate():
            yield kind,data,pos

    stream = stream | Transformer( '//select[@id="field-%s"]' % field ).filter(select_helper)
    stream = stream | Transformer( '//input[@id="field-%s"]' % field ).filter(helper)
    return stream


def remove_header(stream, field):
    """ Removes the display from the ticket properties """
    stream = stream | \
        Transformer('//th[@id="h_%s"]' % field).replace(tag.th(id="h_%s" % field))
    stream = stream | \
        Transformer('//td[@headers="h_%s"]' % field).replace(tag.th(id="h_%s" % field))
    return stream

def remove_changelog(stream, field):
    """ Removes entries from the visible changelog"""
    def helper(field_stream):
        s =  Stream(field_stream)
        f = s.select('//strong/text()').textOf()
        if field != f: #if we are the field just skip it
            #identity stream filter
            for kind, data, pos in s:
                yield kind, data, pos
    stream = stream | Transformer('//ul[@class="changes"]/li').filter(helper)
    return stream
    

def hide_field(stream , field):
    """ Replaces a field from the form area with an input type=hidden"""
    def helper (field_stream):
        type = Stream(field_stream).select('@type').textOf()
        if type == 'checkbox':
            if Stream(field_stream).select('@checked').textOf() == "checked":
                value = 1
            else:
                value = 0
        else:
            value = Stream(field_stream).select('@value').textOf()
        name = Stream(field_stream).select('@name').textOf()
        for kind,data,pos in tag.input( value=value,
                                        type="hidden", name=name).generate():
            yield kind,data,pos

    def select_helper(stream):
        s = Stream(stream)
        name = s.select('@name').textOf()
        opt = s.select('//option[@selected]')
        if not opt: s.select('//option[position()=1]')
        text = opt.select("text()").textOf()
        value = s.select('@value').textOf()
        if not value: value = text
        for kind,data,pos in tag.input(value=value, name=name, type="hidden").generate():
            yield kind,data,pos

    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(" ")
    stream = stream | Transformer('//input[@id="field-%s"]' % field).filter(helper)
    stream = stream | Transformer('//select[@id="field-%s"]' % field).filter(select_helper)

    return remove_changelog(remove_header(stream , field), field)

def remove_field(stream , field):
    """ Removes a field from the form area"""
    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(" ")
    stream = stream | Transformer('//*[@id="field-%s"]' % field).replace(" ")
    return remove_changelog(remove_header(stream , field), field)

def istrue(v, otherwise=None):
    if isinstance(v, bool):
        return v
    if str(v).lower() in ('yes', 'true', '1', 'on'):
        return True
    if not otherwise:
        return False
    return otherwise

csection = 'field settings'

class TicketTweaks(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)    
    ## ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        self.log.debug('IN BlackMagic')
        if not filename == "ticket.html":
            self.log.debug('Not a ticket returning')
            return stream
        fields = self.config.getlist(csection, 'fields', [])
        self.log.debug('read enchants = %r' % fields)
        for field in fields:
            self.log.debug('starting : %s' % field)
            disabled = False
            hidden = False
            hide_summary = False
            remove = False
            perms = self.config.getlist(csection, '%s.permission' % field, [])
            self.log.debug('read permission config: %s has %s' % (field, perms))
            for (perm, denial) in [s.split(":") for s in perms] :
                perm = perm.upper()
                self.log.debug('testing permission: %s:%s should act= %s' %
                               (field, perm, (not req.perm.has_permission(perm) or perm == "ALWAYS")))
                if (not req.perm.has_permission(perm) or perm == "ALWAYS"): 
                    if denial:
                        denial = denial.lower()
                        if denial == "disable":
                            disabled = True
                        elif denial == "hide":
                            hidden = True
                        elif denial == "remove":
                            remove = True
                        else:
                            disabled = True
                    else:
                        disabled = True
                    
                if disabled or istrue(self.config.get(csection, '%s.disable' % field, False)):
                    self.log.debug('disabling: %s' % field)
                    stream = disable_field(stream, field)

                if self.config.get(csection, '%s.label' % field, None):
                    self.log.debug('labeling: %s' % field)
                    stream = stream | Transformer('//label[@for="field-%s"]' % field).replace(
                        self.config.get(csection, '%s.label' % field)
                    )
                    
                if self.config.get(csection, '%s.notice' % field, None):
                    self.log.debug('noticing: %s' % field)
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).after(
                        tag.br() + tag.small()(
                            tag.em()(
                                Markup(self.config.get(csection, '%s.notice' % field))
                            )
                        )
                    )
                    
                tip = self.config.get(csection, '%s.tip' % field, None)
                if tip:
                    self.log.debug('tipping: %s' % field)
                    stream = stream | Transformer('//div[@id="banner"]').before(
                        tag.script(type="text/javascript", 
                        src=req.href.chrome("blackmagic", "js", "wz_tooltip.js"))()
                    )
                    
                    stream = stream | Transformer('//*[@id="field-%s"]' % field).attr(
                        "onmouseover", "Tip('%s')" % tip.replace(r"'", r"\'")
                    )
                    
                if remove or istrue(self.config.get(csection, '%s.remove' % field, None)):
                    self.log.debug('removing: %s' % field)
                    stream = remove_field(stream, field)

                if hidden or istrue(self.config.get(csection, '%s.hide' % field, None)):
                    self.log.debug('hiding: %s' % field)
                    stream = hide_field(stream, field)
                    
        return stream

    ## ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('blackmagic', resource_filename(__name__, 'htdocs'))]
          
    def get_templates_dirs(self):
        return []    
