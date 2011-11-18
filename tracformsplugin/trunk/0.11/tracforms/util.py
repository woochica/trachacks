# -*- coding: utf-8 -*-

# 2011 Steffen Hoffmann

import htmlentitydefs
import re
import unittest

from codecs          import getencoder
from genshi.builder  import Markup, tag

from trac.resource   import ResourceSystem
from trac.util.datefmt import format_datetime
from trac.util.text  import to_unicode

from api             import _
from compat          import json

__all__ = ['parse_history', 'resource_from_page',
           'xml_escape', 'xml_unescape']


def parse_history(changes, fieldwise=False):
    """Versatile history parser for TracForms.

    Returns either a list of dicts for changeset display in form view or
    a dict of field change lists for stepwise form reset.
    """
    fieldhistory = {}
    history = []
    if not fieldwise == False:
        def _add_change(fieldhistory, field, author, time, old, new):
            if field not in fieldhistory.keys():
                fieldhistory[field] = [{'author': author, 'time': time,
                                        'old': old, 'new': new}]
            else:
                fieldhistory[field].append({'author': author, 'time': time,
                                            'old': old, 'new': new})
            return fieldhistory

    new_fields = None
    for changeset in changes:
        # break down old and new version
        try:
            old_fields = json.loads(changeset.get('old_state', '{}'))
        except ValueError:
            # skip invalid history
            old_fields = {}
            pass
        if new_fields is None:
            # first loop cycle: only load values for comparison next time
            new_fields = old_fields
            last_author = changeset['author']
            last_change = changeset['time']
            continue
        updated_fields = {}
        for field, old_value in old_fields.iteritems():
            new_value = new_fields.get(field)
            if new_value != old_value:
                if fieldwise == False:
                    change = _render_change(old_value, new_value)
                    if change is not None:
                        updated_fields[field] = change
                else:
                    fieldhistory = _add_change(fieldhistory, field,
                                               last_author, last_change,
                                               old_value, new_value)
        for field in new_fields:
            if old_fields.get(field) is None:
                if fieldwise == False:
                    change = _render_change(None, new_fields[field])
                    if change is not None:
                        updated_fields[field] = change
                else:
                    fieldhistory = _add_change(fieldhistory, field,
                                               last_author, last_change,
                                               None, new_fields[field])
        new_fields = old_fields
        history.append({'author': last_author,
                        'time': format_datetime(last_change),
                        'changes': updated_fields})
        last_author = changeset['author']
        last_change = changeset['time']
    return fieldwise == False and history or fieldhistory

def _render_change(old, new):
    rendered = None
    if old and not new:
        rendered = tag(Markup(_("%(value)s reset to default value",
                                value=tag.em(old))))
    elif new and not old:
        rendered = tag(Markup(_("from default value set to %(value)s",
                                value=tag.em(new))))
    elif old and new:
        if len(old) < 20 and len(new) < 20:
            rendered = tag(Markup(_("changed from %(old)s to %(new)s",
                                    old=tag.em(old), new=tag.em(new))))
        else:
            nbsp = tag.br()
            # TRANSLATOR: same as before, but with additional line breaks
            rendered = tag(Markup(_("changed from %(old)s to %(new)s",
                                    old=tag.em(nbsp, old),
                                    new=tag.em(nbsp, new))))
    return rendered

# adapted from code published by Daniel Goldberg on 09-Dec-2008 at
# http://stackoverflow.com/questions/354038
def is_number(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False

# code from an article published by Uche Ogbuji on 15-Jun-2005 at
# http://www.xml.com/pub/a/2005/06/15/py-xml.html
def xml_escape(text):
    enc = getencoder('us-ascii')
    return enc(to_unicode(text), 'xmlcharrefreplace')[0]

# adapted from code published by John J. Lee on 06-Jun-2007 at
# http://www.velocityreviews.com/forums
#   /t511850-how-do-you-htmlentities-in-python.html
unichresc_RE = re.compile(r'&#?[A-Za-z0-9]+?;')

def xml_unescape(text):
    return unichresc_RE.sub(_replace_entities, text)

def _unescape_charref(ref):
    name = ref[2:-1]
    base = 10
    # DEVEL: gain 20 % performance by omitting hex references
    if name.startswith("x"):
        name = name[1:]
        base = 16
    return unichr(int(name, base))

def _replace_entities(match):
    ent = match.group()
    if ent[1] == "#":
        return _unescape_charref(ent)
    repl = htmlentitydefs.name2codepoint.get(ent[1:-1])
    if repl is not None:
        repl = unichr(repl)
    else:
        repl = ent
    return repl

def resource_from_page(env, page):
    resource_realm = None
    resources = ResourceSystem(env)
    for realm in resources.get_known_realms():
        if page.startswith('/' + realm):
            resource_realm = realm
            break
    if resource_realm is not None:
        return (resource_realm,
                re.sub('/' + resource_realm, '', page).lstrip('/'))
    else:
        return page, None


class UnescapeTests(unittest.TestCase):

    def test_unescape_charref(self):
        self.assertEqual(unescape_charref(u"&#38;"), u"&")
        self.assertEqual(unescape_charref(u"&#x2014;"), u"\N{EM DASH}")
        self.assertEqual(unescape_charref(u"—"), u"\N{EM DASH}")

    def test_unescape(self):
        self.assertEqual(unescape(u"&amp; &lt; &mdash; — &#x2014;"),
            u"& < %s %s %s" % tuple(u"\N{EM DASH}"*3)
        )
        self.assertEqual(unescape(u"&a&amp;"), u"&a&")
        self.assertEqual(unescape(u"a&amp;"), u"a&")
        self.assertEqual(unescape(u"&nonexistent;"), u"&nonexistent;")

#    unittest.main()

