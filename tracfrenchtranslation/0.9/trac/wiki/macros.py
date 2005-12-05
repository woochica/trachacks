# -*- coding: utf-8 -*-
#
# Copyright (C) 2005 Edgewall Software
# Copyright (C) 2005 Christopher Lenz <cmlenz@gmx.de>
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
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from trac.config import default_dir
from trac.core import *
from trac.util import escape, format_date
from trac.wiki.api import IWikiMacroProvider, WikiSystem
from trac.wiki.model import WikiPage


class TitleIndexMacro(Component):
    """
    Insère une liste alphabetique de toutes les pages Wiki

    Accèpte un paramètre précisant le préfixe: s'il est fourni, seules les
    pages commencant par ce prefix seront incluses dans la liste résultante.
    S'il n'est pas fournit, toutes les pages seront listées.
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'TitleIndex'

    def get_macro_description(self, name):
        return inspect.getdoc(TitleIndexMacro)

    def render_macro(self, req, name, content):
        prefix = content or None

        wiki = WikiSystem(self.env)
        pages = list(wiki.get_pages(prefix))
        pages.sort()

        buf = StringIO()
        buf.write('<ul>')
        for page in pages:
            buf.write('<li><a href="%s">' % escape(self.env.href.wiki(page)))
            buf.write(escape(page))
            buf.write('</a></li>\n')
        buf.write('</ul>')

        return buf.getvalue()


class RecentChangesMacro(Component):
    """
    Liste toutes les pages qui ont été modifiées récemment, en les regroupant
    par le jour de leur dernière modification.

    La macro accèpte deux paramètres. Le premier est un prefix: s'il est 
    fourni, seules les pages dont le nom débute par ce préfix seront incluses
    dans la liste résultante. Si ce pamarètre est omis, toutes les pages sont
    listées.

    Le second paramètre est une valeur limitant le nombre de pages retournées.
    Par exemple, en spécifiant une limite de 5, seules les dernières 5 pages 
    récemment changées seront incluses dans la liste.
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'RecentChanges'

    def get_macro_description(self, name):
        return inspect.getdoc(RecentChangesMacro)

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

        sql = 'SELECT name, max(time) FROM wiki'
        args = []
        if prefix:
            sql += ' WHERE name LIKE %s'
            args.append(prefix + '%')
        sql += ' GROUP BY name ORDER BY max(time) DESC'
        if limit:
            sql += ' LIMIT %s'
            args.append(limit)
        cursor.execute(sql, args)

        buf = StringIO()
        prevdate = None

        for name, time in cursor:
            date = format_date(time)
            if date != prevdate:
                if prevdate:
                    buf.write('</ul>')
                buf.write('<h3>%s</h3><ul>' % date)
                prevdate = date
            buf.write('<li><a href="%s">%s</a></li>\n'
                      % (escape(self.env.href.wiki(name)), escape(name)))
        if prevdate:
            buf.write('</ul>')

        return buf.getvalue()


class PageOutlineMacro(Component):
    """
    Affiche la structure de la page Wiki courante, chaque élement de la 
    structure intégrant un lien vers la section correspondante

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
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'PageOutline'

    def get_macro_description(self, name):
        return inspect.getdoc(PageOutlineMacro)

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


class ImageMacro(Component):
    """
    Embed an image in wiki-formatted text.
    
    The first argument is the file specification. The file specification may
    reference attachments or files in three ways:
     * `module:id:file`, where module can be either '''wiki''' or '''ticket''',
       to refer to the attachment named ''file'' of the specified wiki page or
       ticket.
     * `id:file`: same as above, but id is either a ticket shorthand or a Wiki
       page name.
     * `file` to refer to a local attachment named 'file'. This only works from
       within that wiki page or a ticket.
    
    Also, the file specification may refer to repository files, using the
    `source:file` syntax.
    
    The remaining arguments are optional and allow configuring the attributes
    and style of the rendered `<img>` element:
     * digits and unit are interpreted as the size (ex. 120, 25%)
       for the image
     * `right`, `left`, `top` or `bottom` are interpreted as the alignment for
       the image
     * `nolink` means without link to image source.
     * `key=value` style are interpreted as HTML attributes for the image
     * `key:value` style are interpreted as CSS style indications for the image
    
    Examples:
    {{{
        [[Image(photo.jpg)]]                           # simplest
        [[Image(photo.jpg, 120px)]]                    # with size
        [[Image(photo.jpg, right)]]                    # aligned by keyword
        [[Image(photo.jpg, nolink)]]                   # without link to source
        [[Image(photo.jpg, align=right)]]              # aligned by attribute
        [[Image(photo.jpg, float:right)]]              # aligned by style
        [[Image(photo.jpg, float:right, border:solid 5px green)]] # 2 style specs
    }}}
    
    You can use image from other page, other ticket or other module.
    {{{
        [[Image(OtherPage:foo.bmp)]]    # if current module is wiki
        [[Image(base/sub:bar.bmp)]]     # from hierarchical wiki page
        [[Image(#3:baz.bmp)]]           # if in a ticket, point to #3
        [[Image(ticket:36:boo.jpg)]]
        [[Image(source:/images/bee.jpg)]] # straight from the repository!
        [[Image(htdocs:foo/bar.png)]]   # image file in project htdocs dir.
    }}}
    
    ''Adapted from the Image.py macro created by Shun-ichi Goto
    <gotoh@taiyo.co.jp>''
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'Image'

    def get_macro_description(self, name):
        return inspect.getdoc(ImageMacro)

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
        size_re = re.compile('^[0-9]+%?$')
        align_re = re.compile('^(?:left|right|top|bottom)$')
        keyval_re = re.compile('^([-a-z0-9]+)([=:])(.*)')
        quoted_re = re.compile("^(?:\";|')(.*)(?:\";|')$")
        attr = {}
        style = {}
        nolink = False
        for arg in args[1:]:
            arg = arg.strip()
            if size_re.search(arg):
                # 'width' keyword
                attr['width'] = arg
                continue
            if align_re.search(arg):
                # 'align' keyword
                attr['align'] = arg
                continue
            if arg == 'nolink':
                nolink = True
                continue
            match = keyval_re.search(arg)
            if match:
                key = match.group(1)
                sep = match.group(2)
                val = match.group(3)
                m = quoted_re.search(val) # unquote "..." and '...'
                if m:
                    val = m.group(1)
                if sep == '=':
                    attr[key] = val;
                elif sep == ':':
                    style[key] = val

        # parse filespec argument to get module and id if contained.
        parts = filespec.split(':')
        url = None
        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket']:
                module, id, file = parts
            else:
                raise Exception("%s module ne peut posséder de fichiers joints" % parts[0])
        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in 
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
            if parts[0] in browser_links:   # source:path
                module, file = parts
                url = self.env.href.browser(file)
                raw_url = self.env.href.browser(file, format='raw')
                desc = filespec
            else: # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                id, file = parts
                if id and id[0] == '#':
                    module = 'ticket'
                    id = id[1:]
                elif id == 'htdocs':
                    raw_url = url = self.env.href.chrome('site', file)
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
                raise Exception('Impossible de référencer un fichier joint '
                                'depuis cet endroit') 
            else:
                raise Exception('Pas de définition de fichier reçue')
        if not url: # this is an attachment
            from trac.attachment import Attachment
            attachment = Attachment(self.env, module, id, file)
            url = attachment.href()
            raw_url = attachment.href(format='raw')
            desc = attachment.description
        for key in ['title', 'alt']:
            if desc and not attr.has_key(key):
                attr[key] = desc
        a_style = 'padding:0; border:none' # style of anchor
        img_attr = ' '.join(['%s="%s"' % x for x in attr.iteritems()])
        img_style = '; '.join(['%s:%s' % x for x in style.iteritems()])
        result = '<img src="%s" %s style="%s" />' \
                 % (raw_url, img_attr, img_style)
        if not nolink:
            result = '<a href="%s" style="%s">%s</a>' % (url, a_style, result)
        return result


class MacroListMacro(Component):
    """Affiche une liste de toutes les macros Wiki installées, en incluant leur
    éventuelle documentation.
    
    Il est également possible d'indiquer le nom d'une macro particulière comme 
    argument. Dans ce cas, seule la documentation de cette macro sera affichée.
    
    Si l'option `PythonOptimize` est activée poour mod_python, cette macro 
    ne sera pas capable d'afficher quelque documentation que ce soit sur les 
    autres macros. 
    """
    implements(IWikiMacroProvider)

    def get_macros(self):
        yield 'MacroList'

    def get_macro_description(self, name):
        return inspect.getdoc(MacroListMacro)

    def render_macro(self, req, name, content):
        from trac.wiki.formatter import wiki_to_html
        from trac.wiki import WikiSystem
        buf = StringIO()
        buf.write("<dl>")

        wiki = WikiSystem(self.env)
        for macro_provider in wiki.macro_providers:
            for macro_name in macro_provider.get_macros():
                if content and macro_name != content:
                    continue
                buf.write("<dt><code>[[%s]]</code></dt>" % escape(macro_name))
                description = macro_provider.get_macro_description(macro_name)
                if description:
                    buf.write("<dd>%s</dd>" % wiki_to_html(description,
                                                           self.env, req))

        buf.write("</dl>")
        return buf.getvalue()


class UserMacroProvider(Component):
    """Ajoute les macros fournies sous forme de fichiers source Python à partir
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
                                   filename, e)

    def get_macro_description(self, name):
        return inspect.getdoc(self._load_macro(name))

    def render_macro(self, req, name, content):
        module = self._load_macro(name)
        try:
            return module.execute(req and req.hdf, content, self.env)
        except Exception, e:
            self.log.error('Wiki macro %s failed (%s)' % (name, e))
            raise e

    def _load_macro(self, name):
        for path in (self.env_macros, self.site_macros):
            macro_file = os.path.join(path, name + '.py')
            if os.path.isfile(macro_file):
                return imp.load_source(name, macro_file)
        raise TracError, 'Macro %s non trouvée' % name
