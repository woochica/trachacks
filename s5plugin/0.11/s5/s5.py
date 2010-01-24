# s5 plugin

import re
from trac.config import Option
from trac.core import *
from trac.mimeview.api import IContentConverter
from trac.web.chrome import ITemplateProvider, add_stylesheet, Chrome
from trac.web.main import IRequestHandler
from trac.wiki.api import IWikiMacroProvider
from trac.wiki.formatter import wiki_to_html
from trac.wiki.model import WikiPage
from trac.util.html import escape, plaintext, Markup

class S5Renderer(Component):
    implements(ITemplateProvider, IRequestHandler, IWikiMacroProvider,
               IContentConverter)

    heading_re = re.compile(r'^==\s*(?P<slide>.*?)\s*==$|^=\s*(?P<title>.*?)\s*=$')
    fixup_re = re.compile(r'^=(\s*.*?\s*)=$', re.S|re.M)
    fixup_images_re = re.compile(r'\[\[Image\(([^:]*?)\)\]\]')

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match('^/s5/(.*)', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return 1

    def process_request(self, req):

        default_theme = self.config['s5slideshow'].get('default_theme',
                                                       'default')
        page = req.args.get('page', None)
        location = req.args.get('location', None)
        theme = req.args.get('theme', default_theme)

        if not page:
            raise TracError('Invalid S5 template')

        page = WikiPage(self.env, name=page)
        if not page.exists:
            raise TracError('Invalid S5 template "%s"' % page.name)

        page_text = self.fixup_images_re.sub(r'[[Image(wiki:%s:\1)]]'
                                             % page.name, page.text)

        in_section = -1
        text = ''
        title = ''
        html_title = ''
        title_page = ''
        handout = ''
        slides = []

        def htmlify(text):
            return wiki_to_html(text, self.env, req)

        for line in page_text.splitlines():
            match = self.heading_re.match(line)
            if match:
                # Insert accumulated text into appropiate location
                if in_section == 1:
                    title_page = htmlify(text)
                elif in_section == 2:
                    text = self.fixup_re.sub(r'\1', text)
                    slides.append({'body': htmlify(text), 'handout': htmlify(handout)})

                if match.lastgroup == 'title':
                    title = match.group(match.lastgroup)
                    html_title = htmlify(title)
                    title = plaintext(html_title)
                    in_section = 1
                else:
                    in_section = 2
                text = ''

            text += line + '\n'

        if in_section == 1:
            title_page = htmlify(text)
        elif in_section == 2:
            text = self.fixup_re.sub(r'\1', text)
            slides.append({'body': htmlify(text), 'handout': htmlify(handout)})

        data = {}
        data['theme'] = theme
        data['title'] = title
        data['html_title'] = html_title
        data['location'] = location
        data['title_page'] = title_page
        data['slides'] = slides

        return 's5.html', data, 'text/html'

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('s5', resource_filename(__name__, 'htdocs'))]

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'SlideShow'

    def get_macro_description(self, name):
        return """Allow the current Wiki page to be viewed as an S5 slideshow. The theme can be specied using the argument ''theme=<theme>''. If the theme is not specified, then the default theme will be used. The available themes are blue, default, dokuwiki, flower, i18n, pixel, and yatil.
        """

    def expand_macro(self, formatter, name, content):
        match = re.match('^/wiki/(.*)', formatter.req.path_info)
        if match:
            return Markup("""
                    <a href="%s%s">
                    <img style="float: right;" src="%s/icon.png" title="View as presentation"/>
                </a>
                """% (formatter.href('s5', match.group(1)), content and '?' + content or '',
                      formatter.href('chrome', 's5')))

    # IContentConverter methods
    def get_supported_conversions(self):
        opt = self.env.config.getbool('s5slideshow', 'show_content_conversion',                                       'true')
        if opt:
            yield ('s5', 'Slideshow', 's5', 'text/x-trac-wiki',
                   'text/html;style=s5', 8)

    def convert_content(self, req, mimetype, content, key):
        template, data, content_type = self.process_request(req)
        output = Chrome(self.env).render_template(req, template, data,
                                                  'text/html')
        return output, content_type
