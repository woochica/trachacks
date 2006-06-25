# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Edgewall Software
# Copyright (C) 2005-2006 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Christopher Lenz <cmlenz@gmx.de>

import imp
import inspect
import os
import re
try:
    set
except NameError:
    from sets import Set as set
from StringIO import StringIO

from trac.config import default_dir
from trac.core import *
from trac.util import sorted
from trac.util.datefmt import format_date
from trac.util.markup import escape, html, Markup
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage
from trac.web.chrome import add_stylesheet


class WikiMacroBase(Component):
    u"""Classe abstraite de base pour toutes les macros Wiki."""
    implements(IWikiMacroProvider)
    abstract = True

    def get_macros(self):
        """Yield the name of the macro based on the class name."""
        name = self.__class__.__name__
        if name.endswith('Macro'):
            name = name[:-5]
        yield name

    def get_macro_description(self, name):
        """Return the subclass's docstring."""
        return inspect.getdoc(self.__class__)

    def render_macro(self, req, name, content):
        raise NotImplementedError


class TitleIndexMacro(WikiMacroBase):
    u"""Insère une liste alphabetique de toutes les pages Wiki
    
    Accèpte un paramètre précisant le préfixe: s'il est fourni, seules les
    pages commencant par ce prefix seront incluses dans la liste résultante.
    S'il n'est pas fournit, toutes les pages seront listées.
    """

    def render_macro(self, req, name, content):
        prefix = content or None

        wiki = WikiSystem(self.env)

        return html.UL([html.LI(html.A(wiki.format_page_name(page),
                                       href=req.href.wiki(page)))
                        for page in sorted(wiki.get_pages(prefix))])


class RecentChangesMacro(WikiMacroBase):
    u"""Liste toutes les pages qui ont été modifiées récemment, en les regroupant
    par le jour de leur dernière modification.

    La macro accèpte deux paramètres. Le premier est un prefix: s'il est 
    fourni, seules les pages dont le nom débute par ce préfix seront incluses
    dans la liste résultante. Si ce pamarètre est omis, toutes les pages sont
    listées.

    Le second paramètre est une valeur limitant le nombre de pages retournées.
    Par exemple, en spécifiant une limite de 5, seules les dernières 5 pages 
    récemment changées seront incluses dans la liste.
    """

    def render_macro(self, req, name, content):
        prefix = limit = None
        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) > 0:
                prefix = argv[0]
                if len(argv) > 1:
                    limit = int(argv[1])

        db = self.env.get_db_cnx()
        cursor = db.cursor()

        sql = 'SELECT name, max(time) AS max_time FROM wiki'
        args = []
        if prefix:
            sql += ' WHERE name LIKE %s'
            args.append(prefix + '%')
        sql += ' GROUP BY name ORDER BY max_time DESC'
        if limit:
            sql += ' LIMIT %s'
            args.append(limit)
        cursor.execute(sql, args)

        entries_per_date = []
        prevdate = None
        for name, time in cursor:
            date = format_date(time)
            if date != prevdate:
                prevdate = date
                entries_per_date.append((date, []))
            entries_per_date[-1][1].append(name)

        wiki = WikiSystem(self.env)
        return html.DIV([html.H3(date) +
                         html.UL([html.LI(html.A(wiki.format_page_name(name),
                                                 href=req.href.wiki(name)))
                                    for name in entries])
                         for date, entries in entries_per_date])


class PageOutlineMacro(WikiMacroBase):
    u"""
    Affiche la structure de la page Wiki courante, chaque élement de la 
    structure intégrant un lien vers la section correspondante.

    Cette macro accèpte trois paramètes optionnels: 

     * Le premier est un nombre ou un intervalle qui permet de configurer 
       les niveaux minimal et maximal des sous-sections qui doivent etre   
       inclus dans la structure generee. Par exemple, l'utilisation
       de "1" permettra de n'inclure que les sous-sections de premier 
       niveau dans la structure. L'utilisation de "2-3" générera une 
       structure contenant toutes les sous-sections de niveau 2 et 3, 
       sous forme d'une liste imbriquée. Par défaut, toutes les 
       sous-sections sont incluses.
     * Le second paramètre peut être utilisé pour préciser un titre (par défaut,
       aucun titre).
     * Le troisième paramètre permet de choisir le style de la présentation. Il 
       peut prendre les valeurs '''inline''' ou '''pullout''' (par défaut, 
       '''pullout'''). Le style '''inline''' permet d'intégrer la présentation 
       au contenu de la page, alors que '''pullout''' permet de placer la 
       structure dans un cadre qui est accollé sur la droite du reste du 
       contenu de la page.
    """

    def render_macro(self, req, name, content):
        from trac.wiki.formatter import wiki_to_outline
        min_depth, max_depth = 1, 6
        title = None
        inline = 0
        if content:
            argv = [arg.strip() for arg in content.split(',')]
            if len(argv) > 0:
                depth = argv[0]
                if depth.find('-') >= 0:
                    min_depth, max_depth = [int(d) for d in depth.split('-', 1)]
                else:
                    min_depth, max_depth = int(depth), int(depth)
                if len(argv) > 1:
                    title = argv[1].strip()
                    if len(argv) > 2:
                        inline = argv[2].strip().lower() == 'inline'

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        pagename = req.args.get('page') or 'WikiStart'
        page = WikiPage(self.env, pagename)

        buf = StringIO()
        if not inline:
            buf.write('<div class="wiki-toc">')
        if title:
            buf.write('<h4>%s</h4>' % escape(title))
        buf.write(wiki_to_outline(page.text, self.env, db=db,
                                  max_depth=max_depth, min_depth=min_depth))
        if not inline:
            buf.write('</div>')
        return buf.getvalue()


class ImageMacro(WikiMacroBase):
    u"""
    Intègre une image dans du texte wiki.

    Le premier argument spécifie le fichier image. Le fichier image peut 
    référencer des pièces jointes ou des fichier de trois façons différentes:
     * `module:id:file`, où le module peut être soit '''wiki''' soit '''ticket''',
       pour référencer la pièce jointe nommée ''file'' à la page wiki ou au 
       ticket spécifié.
     * `id:file`: même utilisation le premier point, mais 'id' est soit une 
       référence ticket soit le nom d'une page Wiki.
     * `file` référence une pièce jointe nommée 'file'. Cette syntaxe ne 
       fonctionne que depuis une page Wiki ou un ticket.

    De plus, la spécification du fichier peut se référer à des fichiers du 
    dépôt, en utilisant la syntaxe `source:file` (`source:file@rev` fonctionne
    également).

    Les arguments restants sont optionnels and permette de configurer les
    attributs et le style de l'élément image (<img>):
     * les nombres et unités sont interprétés comme la taille (ex. 120, 25%)
       de l'image
     * `right`, `left`, `top` or `bottom` sont interprétés comme le 
       positionnement de l'image, respectivement droite, gauche, haut et bas.
     * `nolink` désactive le lien vers l'image source
     * le style `key=value` est interprété comme des attributs HTML de l'image
     * le style `key:value` est interprété comme des indicateurs CSS de l'image
    
     Exemples:
    {{{
        [[Image(photo.jpg)]]                           # le plus simple
        [[Image(photo.jpg, 120px)]]                    # avec la taille
        [[Image(photo.jpg, right)]]                    # aligné par mot clef
        [[Image(photo.jpg, nolink)]]                   # sans lien vers la source
        [[Image(photo.jpg, align=right)]]              # aligné par un style HTML
    }}}
    
    Vous pouvez utiliser une image jointe à une autre page, un autre ticket ou
    un autre module.
    {{{
        [[Image(OtherPage:foo.bmp)]]    # depuis une page wiki
        [[Image(base/sub:bar.bmp)]]     # depuis une page sous-page wiki
        [[Image(#3:baz.bmp)]]           # depuis un ticket, #3 ticket
        [[Image(ticket:36:boo.jpg)]]
        [[Image(source:/images/bee.jpg)]] # référence le dépôt
        [[Image(htdocs:foo/bar.png)]]   # fichier image depuis le rép. statique.
    }}}
    
    ''Basé sur une adaptation de la macro Image.py créée par Shun-ichi Goto
    <gotoh@taiyo.co.jp>''
    """

    def render_macro(self, req, name, content):
        # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("Aucun argument")
        filespec = args[0]
        size_re = re.compile('[0-9]+%?$')
        attr_re = re.compile('(align|border|width|height|alt'
                             '|title|longdesc|class|id|usemap)=(.+)')
        quoted_re = re.compile("(?:[\"'])(.*)(?:[\"'])$")
        attr = {}
        style = {}
        nolink = False
        for arg in args[1:]:
            arg = arg.strip()
            if size_re.match(arg):
                # 'width' keyword
                attr['width'] = arg
                continue
            if arg == 'nolink':
                nolink = True
                continue
            match = attr_re.match(arg)
            if match:
                key, val = match.groups()
                m = quoted_re.search(val) # unquote "..." and '...'
                if m:
                    val = m.group(1)
                if key == 'align':
                    style['float'] = val
                elif key == 'border':
                    style['border'] = ' %dpx solid' % int(val);
                else:
                    attr[str(key)] = val # will be used as a __call__ keyword

        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        url = None
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module ne peut posséder de fichiers "
                                "joints" % parts[0])
        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in 
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
            if parts[0] in browser_links:   # source:path
                module, file = parts
                rev = None
                if '@' in file:
                    file, rev = file.split('@')
                url = req.href.browser(file, rev=rev)
                raw_url = req.href.browser(file, rev=rev, format='raw')
                desc = filespec
            else: # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                id, file = parts
                if id and id[0] == '#':
                    module = 'ticket'
                    id = id[1:]
                elif id == 'htdocs':
                    raw_url = url = req.href.chrome('site', file)
                    desc = os.path.basename(file)
                else:
                    module = 'wiki'
        elif len(parts) == 1:               # attachment
            # determine current object
            # FIXME: should be retrieved from the formatter...
            # ...and the formatter should be provided to the macro
            file = filespec
            module, id = 'wiki', 'WikiStart'
            path_info = req.path_info.split('/',2)
            if len(path_info) > 1:
                module = path_info[1]
            if len(path_info) > 2:
                id = path_info[2]
            if module not in ['wiki', 'ticket']:
                raise Exception(u'Impossible de référencer un fichier joint '
                                 'depuis cet endroit') 
        else:
            raise Exception(u'Pas de définition de fichier reçue')
        if not url: # this is an attachment
            from trac.attachment import Attachment
            attachment = Attachment(self.env, module, id, file)
            url = attachment.href(req)
            raw_url = attachment.href(req, format='raw')
            desc = attachment.description
        for key in ['title', 'alt']:
            if desc and not attr.has_key(key):
                attr[key] = desc
        if style:
            attr['style'] = '; '.join(['%s:%s' % (k, escape(v))
                                       for k, v in style.iteritems()])
        result = Markup(html.IMG(src=raw_url, **attr)).sanitize()
        if not nolink:
            result = html.A(result, href=url, style='padding:0; border:none')
        return result


class MacroListMacro(WikiMacroBase):
    u"""Affiche une liste de toutes les macros Wiki installées, en incluant leur
    éventuelle documentation.
    
    Il est également possible d'indiquer le nom d'une macro particulière comme 
    argument. Dans ce cas, seule la documentation de cette macro sera affichée.
    
    Si l'option `PythonOptimize` est activée poour mod_python, cette macro 
    ne sera pas capable d'afficher quelque documentation que ce soit sur les 
    autres macros. 
    """

    def render_macro(self, req, name, content):
        from trac.wiki.formatter import wiki_to_html, system_message
        from trac.wiki import WikiSystem
        wiki = WikiSystem(self.env)

        def get_macro_descr():
            for macro_provider in wiki.macro_providers:
                for macro_name in macro_provider.get_macros():
                    if content and macro_name != content:
                        continue
                    try:
                        descr = macro_provider.get_macro_description(macro_name)
                        descr = wiki_to_html(descr or '', self.env, req)
                    except Exception, e:
                        descr = Markup(system_message(
                            "Error: Can't get description for macro %s" \
                            % macro_name, e))
                    yield (macro_name, descr)

        return html.DL([(html.DT(html.CODE('[[',macro_name,']]')),
                         html.DD(description))
                        for macro_name, description in get_macro_descr()])


class InterTracMacro(WikiMacroBase):
    u"""Genère la liste de tous les prefixes InterTrac connus."""

    def render_macro(self, req, name, content):
        intertracs = {}
        for key, value in self.config.options('intertrac'):
            if '.' in key:
                prefix, attribute = key.split('.', 1)
                intertrac = intertracs.setdefault(prefix, {})
                intertrac[attribute] = value
            else:
                intertracs[key] = value # alias

        def generate_prefix(prefix):
            intertrac = intertracs[prefix]
            if isinstance(intertrac, basestring):
                yield html.TR(html.TD(html.B(prefix)),
                              html.TD('Alias for ', html.B(intertrac)))
            else:
                url = intertrac.get('url', '')
                if url:
                    title = intertrac.get('title', url)
                    yield html.TR(html.TD(html.A(html.B(prefix),
                                                 href=url + '/timeline')),
                                  html.TD(html.A(title, href=url)))

        return html.TABLE(class_="wiki intertrac")(
            html.TR(html.TH(html.EM('Prefix')), html.TH(html.EM('Trac Site'))),
            [generate_prefix(p) for p in sorted(intertracs.keys())])


class TracIniMacro(WikiMacroBase):
    u"""Génère la documentation pour le fichier de configuration de Trac.

    Cette macro est typiquement utilisée dans la page TracIni.
    Les arguments optionnels permettre de filtrer une section particulière
    de configuration et le nom d'une option de cette section.
    Seules les options dont la section et le nom commencent par les filtres
    indiqués sont documentés. 
    """

    def render_macro(self, req, name, filter):
        from trac.config import Option
        from trac.wiki.formatter import wiki_to_html, wiki_to_oneliner
        filter = filter or ''

        sections = set([section for section, option in Option.registry.keys()
                        if section.startswith(filter)])

        return html.DIV(class_='tracini')(
            [(html.H2('[%s]' % section, id='%s-section' % section),
              html.TABLE(class_='wiki')(
                  html.TBODY([html.TR(html.TD(html.TT(option.name)),
                                      html.TD(wiki_to_oneliner(option.__doc__,
                                                               self.env)))
                              for option in Option.registry.values()
                              if option.section == section])))
             for section in sorted(sections)])


class UserMacroProvider(Component):
    u"""Ajoute les macros fournies sous forme de fichiers source Python à partir
    du répertoire `wiki-macros` de l'environnement Trac, ou du répertoire 
    global des macros
    """
    implements(IWikiMacroProvider)

    def __init__(self):
        self.env_macros = os.path.join(self.env.path, 'wiki-macros')
        self.site_macros = default_dir('macros')

    # IWikiMacroProvider methods

    def get_macros(self):
        found = []
        for path in (self.env_macros, self.site_macros):
            if not os.path.exists(path):
                continue
            for filename in [filename for filename in os.listdir(path)
                             if filename.lower().endswith('.py')
                             and not filename.startswith('__')]:
                try:
                    module = self._load_macro(filename[:-3])
                    name = module.__name__
                    if name in found:
                        continue
                    found.append(name)
                    yield name
                except Exception, e:
                    self.log.error('Failed to load wiki macro %s (%s)',
                                   filename, e, exc_info=True)

    def get_macro_description(self, name):
        return inspect.getdoc(self._load_macro(name))

    def render_macro(self, req, name, content):
        module = self._load_macro(name)
        try:
            return module.execute(req and req.hdf, content, self.env)
        except Exception, e:
            self.log.error('Wiki macro %s failed (%s)', name, e, exc_info=True)
            raise

    def _load_macro(self, name):
        for path in (self.env_macros, self.site_macros):
            macro_file = os.path.join(path, name + '.py')
            if os.path.isfile(macro_file):
                return imp.load_source(name, macro_file)
        raise TracError, 'Macro %s non trouvée' % name
