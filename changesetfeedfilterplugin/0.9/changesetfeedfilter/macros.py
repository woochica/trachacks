import inspect
from cStringIO import StringIO

from trac.core import *
from trac.util import escape, Markup
from trac.wiki.api import WikiSystem, IWikiMacroProvider

DEFAULT_CONTENT = '''
{{{
#!ChangesetFilter
# add patterns here
}}}
'''

class ChangesetFeedsMacro(Component):
    implements(IWikiMacroProvider)
    
    def get_macros(self):
        return ['ChangesetFeeds', 'ChangesetFilter']
        
    def get_macro_description(self, name):
        return inspect.getdoc(ListFeedsMacro)

    def render_macro(self, req, name, content):
        if name == 'ChangesetFeeds':
            return self._render_feeds(req, content)
        elif name == 'ChangesetFilter':
            return self._render_filter(req, content)

    def _render_feeds(self, req, content):
        wiki = WikiSystem(self.env)
        prefix = req.args['page'].value
        if not prefix.endswith('/'):
            prefix += '/'
        pages = sorted(page for page in wiki.get_pages(prefix) if page != prefix)
        buf = StringIO()
        print >>buf, '<h1>Available Feeds</h1>'
        if pages:
            print >>buf, '<ul>'
            href = self.env.href
            for page in pages:
                rel_name = page[len(prefix):]
                print >>buf, Markup(
                    '<li><a href="%s">%s</a> <a href="%s">[rss]</a> <a href="%s">[edit]</a></li>',
                    href.wiki(page), rel_name, href.changesetrss(page), href.wiki(page, action='edit')
                )
            print >>buf, '</ul>'
        else:
            print >>buf, '<p>None</p>'
        print >>buf, Markup('''<script type="text/javascript">
        var new_filter = function(form) {
            window.location = '%s'.replace(/deadbeef/, form.page_name.value);
        };
        </script>
        ''', href.wiki(prefix + 'deadbeef', action='edit', text=DEFAULT_CONTENT)
        )
        print >>buf, Markup('''<form onsubmit="new_filter(this); return false;">
            <input type="text" name="page_name">
            <input type="submit" value="Add Filter">
        </form>
        ''')
        return buf.getvalue()

    def _render_filter(self, req, content):
        buf = StringIO()
        page = req.args['page'].value
        href = self.env.href
        print >>buf, Markup('<a href="%s">[rss]</a><br>', href.changesetrss(page))
        idx = page.rstrip('/').rfind('/')
        if idx != -1:
            print >>buf, Markup('<a href="%s">[feed list]</a><br>', href.wiki(page[:idx]))
        print >>buf, Markup('<h1>Filter Patterns:</h1>'
            '<pre class="wiki">%s</pre>',
            content
        )
        return buf.getvalue()

