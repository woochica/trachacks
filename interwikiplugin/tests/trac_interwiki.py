
"""
Checks that interwiki Trac support works by simulating a user (browser) session and
verifying results.

Requires a running Trac instance. Its url should be passed in as a first argument, 
e.g.: http://localhost:8000/trac-trac/wiki/.

Required Python libraries: mechanize (easy_install mechanize).

Assumes Trac site's configuration file (trac.ini) 
has been augmented with the following text:

[interwiki]
Wiki=http://c2.com/cgi/wiki?
WikiPedia=http://en.wikipedia.org/wiki/
Google=http://www.google.com/search?q=

The script works like this:

    1. Creates a page on wiki and fills it with valid and bogus inter-wiki
    references.
    2. Loads page to verify the links were rendered correctly.

"""

import sys
import mechanize

baseurl = None
TEMP_PAGE = 'Sandbox/InterWikiTest' # wiki page that will be used for testing
SAMPLE_TEXT = '''

This is a test page for interwiki links.

Link link:wiki:Foo.
Link link:WIKI:Foo.
Link [link:wiki:page title text].
Link link:wikipedia:Wiki.

Non-link link:wikipudia:Wiki.
Non-link link:wikipedia.
Non-link [link:stiki:page title text].

'''

expectedLinkLines = '''\
Link <a class="ext-link" href="http://c2.com/cgi/wiki?Foo"><span class="icon"></span>wiki:Foo</a>.
Link <a class="ext-link" href="http://c2.com/cgi/wiki?Foo"><span class="icon"></span>WIKI:Foo</a>.
Link <a class="ext-link" href="http://c2.com/cgi/wiki?page"><span class="icon"></span>wiki:title text</a>.
Link <a class="ext-link" href="http://en.wikipedia.org/wiki/Wiki"><span class="icon"></span>wikipedia:Wiki</a>.
Non-link link:wikipudia:Wiki.
Non-link link:wikipedia.
Non-link [link:stiki:page title text].'''.split('\n')

#import logging
#logfile = open('tests.log', 'wt')
#logger = logging.getLogger("ClientCookie")
#logger.addHandler(logging.StreamHandler(logfile))
#logger.setLevel(logging.INFO)

def edit_sandbox_page(page_name, page_text):
    b = mechanize.Browser()
    #b.set_debug_http(True)
    #b.set_debug_responses(True)
    url = baseurl + page_name
    b.open(url + '?action=edit')
    b.select_form(predicate=lambda f: f.attrs.get('id') == 'edit')
    if page_text <> b['text']:
        b['text'] = page_text
        b.submit(name='save')
        assert b.viewing_html()
        assert b.geturl() == url, b.geturl()
    else:
        b.open(url)
    html = b.response().read()
    return html

def testWikiLinks():
    print 'Publishing test content on page %s' % TEMP_PAGE
    html = edit_sandbox_page(TEMP_PAGE, SAMPLE_TEXT)
    print 'Page changed OK, checking results'
    #open('z.html', 'wt').write(html)
    for line in expectedLinkLines:
        assert line in html, line
    print 'Test passed, see %s%s wiki page' % (baseurl, TEMP_PAGE)

if __name__=='__main__':
    if len(sys.argv) <> 2:
        import os.path
        program = os.path.basename(sys.argv[0])
        print 'Usage: %s <wiki url>' % program
        print 'Example: %s http://localhost:8000/trac-trac/wiki/' % program
        sys.exit(1)
    baseurl = sys.argv.pop(1)
    if not baseurl.endswith('/'):
        baseurl = baseurl + '/'
    testWikiLinks()
