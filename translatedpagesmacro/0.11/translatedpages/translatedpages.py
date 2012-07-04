# -*- coding: utf-8 -*-

""" Macro to show the translated pages list. """

from trac.core import *
from trac.wiki.api import IWikiMacroProvider
from trac.util.text import to_unicode
from StringIO import StringIO
from trac.wiki.formatter import Formatter
from trac.wiki.model import WikiPage
from trac.wiki.api import WikiSystem, parse_args
from trac.config import Option
import re
import inspect

class TranslatedPagesMacro(Component):
    """
    Macro to show the translated pages list.
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        yield u'TranslatedPages'

    def get_macro_description(self, name):
        return """Macro to show the translated pages list.

Simply calling that macro in a page adds a menu linking to all available translations of a page.

A language page (usually [wiki:TracLanguages]) must provide the language codes as a table
with following entries:
{{{
||<language code>||<language name>||<english name>||<description>||
}}}
The description contains the text displayed above language links in that language
(usually a variant of 'Other languages').
A table title line starting with {{{||=}}} is not parsed.

The Macro accepts arguments as well:
 * '''revision=<num>'''   to specify the version of the base page when last translated, a negative revision indicates that a page needs updating in the status overview table
 * '''outdated=<text>'''  mark the page as outdated with given comment
 * '''silent'''           don't output empty chapter for show options when nothing is shown
    
 * '''showoutdated'''     to show all pages, where revision does not match base revision
 * '''showmissing'''      to show all pages, where translation is missing
 * '''showproblems'''     to show all pages which have problems
 * '''showuntranslated''' to show all untranslated pages
 * '''showstatus'''       to show one big status table
 * '''lang=<code>'''      to restrict output of show outdated, status or missing to a specific language"""

    def parse_macro(self, parser, name, content):
        raise NotImplementedError

    # --

    lang_page_name = Option('translatedpages', 'languages_page', u'TracLanguages',
        """Page name of table containing available languages""")
    page_code = Option('translatedpages', 'template', u'{lang}:{page}',
        """Page name template of translated pages""")
    base_lang = Option('translatedpages', 'base_language', u'En',
        """Base language to be used without prefix/suffix""")
    langcode_re = Option('translatedpages', 'regexp', u'([A-Z][a-z]{1,2}(?:_[A-Z]{2})?)',
        """Regular expression to match a language code""")

    outdated_tx = "<p style=\"background-color:rgb(253,255,221);padding: 10pt; border-color:rgb(128,128,128);border-style: solid; border-width: 1px;\">%s</p>\n"

    macro_re = re.compile(u"\[\[TranslatedPages(?:\((.+)\))?\]\]")
    revision_re = re.compile(u"\[\[TranslatedPages(?:\(.*?revision=(-?\d+).*?\))?\]\]")
    outdated_re = re.compile(u"\[\[TranslatedPages(?:\(.*?outdated=(.*)\))?\]\]")

    def __init__(self):
        self.langpage_re = re.compile(u"^\|\|"+ self.langcode_re + u"\|\|(.+?)\|\|(.+?)\|\|(.+?)\|\|$")
        self.languages_page_version = 0
        self._update_languages()
        self.template_re = re.compile(self.page_code \
            .replace('{lang}', r'(?P<lang>%s)' % self.langcode_re) \
            .replace('{page}', r'(?P<page>.+?)') + '$')

    def _parse_languages_list(self, text):
        langs = {}
        descr = {}
        langse = {}
        for line in text.replace('\r','').split(u'\n'):
            regres = self.langpage_re.search(line)
            if regres == None:
                if not line.startswith(u'||=') and len(line) > 0:
                    self.env.log.warn(
                        u"Wrong line syntax while parsing languages list: %s" % line)
            else:
                code = regres.group(1)
                name = regres.group(2)
                engname = regres.group(3)
                desc = regres.group(4)
                self.env.log.debug("Adding language %s -> %s [%s] (%s)" \
                    % (code, name, engname, desc))
                langs[code] = name
                descr[code] = desc
                langse[code] = engname
        return (langs, descr, langse)

    def _update_languages(self):
        languages_page = WikiPage(self.env, self.lang_page_name)
        if not languages_page.exists:
            self.env.log.warn(u"Can't find page %s" % self.lang_page_name)
            self.languages = {}
            self.languages_page_version = 0
        else:
            if languages_page.version > self.languages_page_version:
                (self.languages, self.description, self.languagesbase) = \
                    self._parse_languages_list(languages_page.text)
                self.languages_page_version = languages_page.version

    def _get_language_name(self, lang_code):
        self._update_languages()
        return self.languages.get(lang_code, lang_code)

    def _get_translated_page(self, prefix, name, lang_code):
        if lang_code != self.base_lang:
            name = self.page_code.replace('{lang}', lang_code) \
                                 .replace('{page}', name)
        return prefix + name

    def _get_page_info(self, page_name):
        m = self.template_re.search(page_name)
        if m:
            page, lang = m.group('page'), m.group('lang')
            prefix = m.start()
        else:
            page = page_name
            lang = self.base_lang
            prefix = 0
            pages = WikiSystem(self.env).get_pages()
            for testpage in pages:
                m = self.template_re.search(testpage)
                if m and page_name == self._get_translated_page( \
                    testpage[:m.start()], m.group('page'), lang):
                        page = m.group('page')
                        prefix = m.start()
                        break
        return (page_name[:prefix], page, lang)

    def _get_translations(self, prefix, base_page_name):
        res = []
        for l in sorted(self.languages.keys()):
            tr = self._get_translated_page(prefix, base_page_name, l);
            if WikiSystem(self.env).has_page(tr):
                res.append(l)
        return res

    def _get_outdated(self, lang):
        if lang != None:
            langd = lang
            if self.languagesbase.has_key(lang):
                langd = self.languagesbase[lang]
            res = u"== Outdated pages for %s ==\n" % langd
        else:
            res = u"== Outdated pages ==\n"
        found = 0;
        for page in sorted(WikiSystem(self.env).get_pages()):
            pagetext = WikiPage(self.env, page).text
            regres = self.revision_re.search(pagetext)
            out = self.outdated_re.search(pagetext)
            outcode = ""
            outver = ""
            prefix, base_page_name, lang_code = self._get_page_info(page)
            if out != None and out.group(1) != None and (lang == None \
            or lang == lang_code or lang_code == self.base_lang):
                outcode = "{{{%s}}}" % out.group(1).replace("\,",",")
            if regres != None and regres.group(1) != None:
                if lang_code != self.base_lang and (lang == None or lang == lang_code):
                    newver = WikiPage(self.env, base_page_name).version
                    oldver = abs(int(regres.group(1)))
                    if(newver != oldver):
                        outver = "[wiki:/%s?action=diff&old_version=%s @%s-@%s]" \
                        % (base_page_name, oldver, oldver, newver)
            if outcode != "" or outver != "":
                res += "|| [wiki:/%s] || %s || %s ||\n" % (page, outver, outcode)
                found += 1

        if found == 0:
            res += u'none\n'
        return res

    def _get_missing(self, lang):
        res = ""
        base_pages = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            for line in WikiPage(self.env, page).text.replace('\r','').split(u'\n'):
                regres = self.macro_re.search(line)
                if regres != None:
                    (prefix, base_page_name, lang_code) = self._get_page_info(page)
                    basename = self._get_translated_page(prefix, \
                        base_page_name, self.base_lang)
                    if not basename in base_pages:
                        base_pages.append(basename)
        langs = []
        if lang != None:
            langs = [lang]
        else:
            langs = self.languages.keys()
            langs.sort()
        for l in langs:
            reslang = ""
            for base_page in base_pages:
                (prefix, page, lang_code) = self._get_page_info(base_page)
                tr = self._get_translated_page(prefix, page, l);
                if not WikiSystem(self.env).has_page(tr):
                    reslang += " * [wiki:/%s]\n" % tr
            if len(reslang) > 0:
                langd = l
                if self.languagesbase.has_key(l):
                    langd = self.languagesbase[l]
                res += u"== Missing pages for %s ==\n%s" % (langd, reslang)

        if len(res) == 0:
            res += u'== Missing pages ==\nnone\n'
        return res

    def _get_untranslated(self, silent):
        res = ""
        for page in sorted(WikiSystem(self.env).get_pages()):
            if self.macro_re.search(WikiPage(self.env, page).text) == None:
                res += " * [wiki:/%s]\n" % page

        if len(res) == 0:
            if(silent):
                return u" "
            res = u'none\n'
        return "== Untranslated pages ==\n"+res

    def _check_args(self, page, argstr, lang_code):
        if argstr == None or len(argstr) == 0:
            if lang_code != self.base_lang:
                return "||[wiki:/%s]|| ||No revision specified for translated page\n" \
                    % page
            else:
                return ""
        resargs = ""
        args, kw = parse_args(argstr)
        show = False
        for arg in args:
            if arg == 'showoutdated' or arg == 'showuntranslated' or \
                arg == 'showmissing' or arg == 'showstatus' or arg == 'showproblems':
                    show = True;
            elif arg != 'silent':
                resargs += "||[wiki:/%s]||%s||unknown argument '%s'||\n" % (page, argstr, arg)
        for arg in kw.keys():
            if arg == 'lang':
                if not ('showoutdated' in args or 'showmissing' in args or \
                    'showstatus' in args):
                        resargs += "||[wiki:/%s]||%s||'lang' argument without proper show argument'||\n" \
                            % (page, argstr)
                elif not self.languages.has_key(kw[arg]):
                    resargs += "||[wiki:/%s]||%s||'lang'='%s' argument uses unknown language||\n" \
                        % (page, argstr, kw[arg])
            elif arg == 'revision':
                try:
                    int(kw[arg])
                    #if int(kw[arg]) < 0:
                    #    resargs += "||[wiki:/%s]||%s||'revision'='%s' is no positive value||\n" \
                    #        % (page, argstr, kw[arg])
                except:
                    resargs += "||[wiki:/%s]||%s||'revision'='%s' is no integer value||\n" \
                        % (page, argstr, kw[arg])
                if show:
                    resargs += "||[wiki:/%s]||%s||'revision'='%s' used with show argument||\n" \
                        % (page, argstr, kw[arg])
                elif lang_code == self.base_lang:
                    resargs += "||[wiki:/%s]||%s||Revision specified for base page\n" \
                        % (page, argstr)
            elif arg != 'outdated':
                resargs += "||[wiki:/%s]||%s||unknown argument '%s'='%s'||\n" \
                    % (page, argstr, arg, kw[arg])
        if lang_code != self.base_lang and not kw.has_key(u'revision') and not show:
            resargs += "||[wiki:/%s]||%s||No revision specified for translated page\n" \
                % (page, argstr)
        return resargs

    def _get_problems(self, silent):
        res = u""
        resargs = u""
        respages = u""
        base_pages = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            for line in WikiPage(self.env, page).text.replace('\r','').split(u'\n'):
                regres = self.macro_re.search(line)
                if regres != None:
                    (prefix, base_page_name, lang_code) = self._get_page_info(page)
                    basename = self._get_translated_page(prefix, \
                        base_page_name, self.base_lang)
                    if not basename in base_pages:
                        base_pages.append(basename)
                    resargs += self._check_args(page, regres.group(1), lang_code)
                    if self.languages.get(lang_code, None) == None:
                      respages += "||[wiki:/%s]||Translated page language code unknown||\n" % page

        base_pages.sort()
        for base_page in base_pages:
            (prefix, page, lang_code) = self._get_page_info(base_page)
            translations = self._get_translations(prefix, page)
            basever = 0;
            if not self.base_lang in translations:
                respages += "||[wiki:/%s]||Base language is missing for translated pages||\n" % base_page
            else:
                basever = WikiPage(self.env, base_page).version
            for translation in translations:
                transpage = self._get_translated_page(prefix, page, translation)
                regres = self.macro_re.search(WikiPage(self.env, transpage).text)
                if regres != None:
                    argstr = regres.group(1)
                    if argstr != None and len(argstr) > 0:
                         args, kw = parse_args(argstr)
                         try:
                             rev = int(kw[u'revision'])
                             if rev != 0 and rev > basever:
                                 respages += "||[wiki:/%s]||Revision %s is higher than base revision %s||\n" \
                                     % (transpage, rev, basever)
                         except:
                             pass
                else:
                    respages += "||[wiki:/%s]||Translated page misses macro 'TranslatedPages'||\n" % transpage
        
        if len(resargs):
            res += u"=== Errors in supplied arguments ===\n||= Page =||= Arguments =||= Issue =||\n"+resargs
        if len(respages):
            res += u"=== Errors in page structure ===\n||= Page =||= Issue =||\n"+respages
        
        if not len(res):
            if(silent):
                return u" "
            res = u'none\n'
        return u"== Problem pages ==\n" + res;

    def _get_status(self, lang):
        res = ""

        base_pages = []
        langs = []
        errors = []
        for page in sorted(WikiSystem(self.env).get_pages()):
            for line in WikiPage(self.env, page).text.replace('\r','').split(u'\n'):
                regres = self.macro_re.search(line)
                if regres != None:
                    (prefix, base_page_name, lang_code) = self._get_page_info(page)
                    basename = self._get_translated_page(prefix, \
                        base_page_name, self.base_lang)
                    if not basename in base_pages:
                        base_pages.append(basename)
                    if len(self._check_args(page, regres.group(1), lang_code)) > 0:
                        errors.append(page)
                    if not lang_code in langs:
                        langs.append(lang_code)
        
        if lang != None:
            langs = [lang]
        else:
            langs.sort()
            res += "\n||= Page =||= " + (" =||= ".join(langs)) + "=||\n"
        base_pages.sort()

        for base_page in base_pages:
            (prefix, page, lang_code) = self._get_page_info(base_page)
            basever = 0;
            if WikiSystem(self.env).has_page(base_page):
                basever = WikiPage(self.env, base_page).version
            if lang == None:
                res += "||[wiki:/%s]" % base_page
            for l in langs:
                color = "green"
                transpage = self._get_translated_page(prefix, page, l)
                if transpage in errors:
                    color = "red"
                elif WikiSystem(self.env).has_page(transpage):
                    regres = self.macro_re.search(WikiPage(self.env, transpage).text)
                    if regres != None:
                         argstr = regres.group(1)
                         if argstr != None and len(argstr) > 0:
                             args, kw = parse_args(argstr)
                             if u'outdated' in kw:
                                 color = "yellow"
                             elif l != self.base_lang:
                                 try:
                                     rev = int(kw[u'revision'])
                                     if rev != 0 and rev > basever:
                                         color = "red"
                                     elif rev != basever:
                                         color = "yellow"
                                 except:
                                     color = "red"
                    else:
                        color = "red"
                else:
                    color = "grey"
                if lang != None:
                    res += "||$$$%s$$$[wiki:/%s %s]" % (color, transpage, base_page)
                else:
                    res += "||$$$%s$$$[wiki:/%s %s]" % (color, transpage, l)
            res +="||\n"
        
        return res

    def expand_macro(self, formatter, name, args):
        """
        Return a list of translated pages with the native language names.
        The list of languages supported can be configured by adding new
        entries to TracLanguages page. Refer to ISO 639-1 for more information.
        """

        args, kw = parse_args(args)

        # first handle special cases
        show = u"";
        lang = None
        silent = u'silent' in args
        outdated = u""
        if u'lang' in kw:
            lang = kw[u'lang']
        if u'outdated' in kw:
            outdated = self.outdated_tx % kw[u'outdated']
        if u'showproblems' in args:
            show += self._get_problems(silent)
        if u'showstatus' in args:
            show += self._get_status(lang)
        if u'showoutdated' in args:
            show += self._get_outdated(lang)
        if u'showmissing' in args:
            show += self._get_missing(lang)
        if u'showuntranslated' in args:
            show += self._get_untranslated(silent)
        if len(show):
            outshow = StringIO()
            Formatter(self.env, formatter.context).format(show, outshow)
            val = outshow.getvalue()
            val = re.sub('>\$\$\$([a-z]+?)\$\$\$<a class=".*?"', \
                ' style="background-color:\\1"><a style="color:#151B8D"', val)
            # try again more secure in case previous fails due to Wiki engine changes
            val = re.sub('>\$\$\$([a-z]+?)\$\$\$', \
                ' style="background-color:\\1">', val)
            return val

        page_name = formatter.context.resource.id
        prefix, base_page_name, lang_code = self._get_page_info(page_name)

        lang_link_list = []
        for translation in self._get_translations(prefix, base_page_name):
            if translation != lang_code:
                page_name = self._get_translated_page(prefix, base_page_name, translation)
                lang_link_list.append(u"  * [[wiki:/%s|%s]]" % (page_name, \
                    self._get_language_name(translation)))
            else:
                lang_link_list.append(u"  * '''%s'''" % self._get_language_name(translation))

        baselink=""
        if lang_code != self.base_lang and u'revision' in kw:
            basepage = self._get_translated_page(prefix, base_page_name, self.base_lang)
            newver = WikiPage(self.env, basepage).version
            oldver = abs(int(kw[u'revision']))
            if oldver < newver:
                baselink = u"\n  * [[wiki:/%s?action=diff&old_version=%s|@%s - @%s]]" \
                    % (basepage, oldver, oldver, newver)

        if len(lang_link_list) <= 1:
            return outdated;
        out = StringIO()
        Formatter(self.env, formatter.context).format(u'\n'.join(lang_link_list) \
            +baselink, out)

        desc = u"Languages"
        if self.description.has_key(lang_code):
            desc = self.description[lang_code]
        return outdated + u"""
<div class="wiki-toc trac-nav" style="clear:both">
<h4>%s:</h4>
%s
</div>""" % (desc, out.getvalue())
