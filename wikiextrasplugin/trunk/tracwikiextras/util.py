# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2011 Mikael Relbe <mikael@relbe.se>
# All rights reserved.
#
# Copyright (C) 2006 Christian Boos <cboos@neuf.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# Author: Christian Boos <cboos@neuf.fr>
#         Mikael Relbe <mikael@relbe.se>

import re
import string

from genshi.builder import tag
from genshi.core import Markup

from trac.util.compat import sorted


def prepare_regexp(d):
    syms = d.keys()
    syms.sort(lambda a, b: cmp(len(b), len(a)))
    return "|".join([r'%s%s%s'
                     % (r'\b' if re.match(r'\w', s[0]) else '',
                        re.escape(s),
                        r'\b' if re.match(r'\w', s[-1]) else '')
                     for s in syms])


def render_table(items, colspec, render_item, colspace=1):
    try:
        columns = max(int(colspec), 1)
    except Exception:
        columns = 3

    nbsp = Markup('&nbsp;')
    # hdr = [tag.th(nbsp, 'Display'), tag.th('Markup', nbsp)]
    spacer_style = 'width:%dem;border:none' % colspace
    # Find max width to make value cols equally wide
    width = 0
    for i in items:
        if (isinstance(i, str) or isinstance(i, unicode)) and len(i) > width:
            width = len(i)
    value_style = 'border:none'
    #noinspection PyUnusedLocal
    if width:
        # empirical...
        value_style = '%s;width:%dem' % (value_style, int(width*2/3))

    def render_def(s):
        rendered = s and render_item(s) or None
        if isinstance(s, str):
            s = Markup(s.replace('&', '&amp;'))
        return [tag.td(rendered, nbsp, style='border:none'),
                tag.td(tag.kbd(s), style=value_style)]
    
    return tag.table(#tag.tr((hdr + [tag.td(style=spacer_style)]) *
                     #       (columns-1) + hdr),
                     [tag.tr([render_def(s) + [tag.td(style=spacer_style)]
                              for s in row[:-1]] + render_def(row[-1]))
                      for row in group_over(sorted(items), columns)],
                     class_='wiki', style='border:none')


def group_over(iterable, num, predicate=None):
    """Combines the elements produced by the given iterable so that every `n`
    items are returned as a tuple.

    >>> items = [1, 2, 3, 4]
    >>> for item in group(items, 2):
    ...     print item
    (1, 3)
    (2, 4)

    The last tuple is padded with `None` values if its' length is smaller than
    `num`.

    >>> items = [1, 2, 3, 4, 5]
    >>> for item in group(items, 2):
    ...     print item
    (1, 4)
    (2, 5)
    (3, None)

    The optional `predicate` parameter can be used to flag elements that should
    not be packed together with other items. Only those elements where the
    predicate function returns True are grouped with other elements, otherwise
    they are returned as a tuple of length 1:

    >>> items = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> for item in group(items, 2, lambda x: x != 4):
    ...     print item
    (1, 3)
    (2, None)
    (4,)
    (5, 8)
    (6, 9)
    (7, None)
    """
    # This function was inspired by trac.util.presentation.group().
    num = max(num, 1)
    # Split into sections at delimited by predicate
    sections = [] # a list of lists of tuple (flush, [items])
    buf = []
    for item in iterable:
        flush = predicate and not predicate(item)
        if buf and flush:
            sections.append((False, buf))
            buf = []
        if flush:
            sections.append((True, [item]))
        else:
            buf.append(item)
    if buf:
        sections.append((False, buf))
    # Return section by section
    buf = []
    for (flush, items) in sections:
        if flush:
            yield tuple(items)
        else:
            # iterate rows
            rows = len(items) // num
            if len(items) % num:
                rows += 1
            for r in range(0, rows):
                # build column
                for c in range(0, num):
                    p = r + c * rows
                    if p < len(items):
                        buf.append(items[p])
                    else:
                        buf.append(None)
                yield tuple(buf)
                del buf[:]


def reduce_names(names, keep=40):
    """Reduce the number of names in an alphabetically balanced manner.

    The reduction is made on a letter-by-letter basis with the goal to keep a
    balanced number of words with different letters on each position. Longer
    words are removed before shorter, letters between lowest and highest
    order are removed first.

    :param names: List of strings.
    :param keep: Max number of strings to keep.

    :ret: A reduced, alphabetically balanced, list of strings.
    """
    if len(names) < keep:
        return names
    elif keep < 1:
        return []

    def build_tree(names):
        """Create a Huffman tree based on names

        The tree is a dict where keys denotes a letter in the name, and the
        value is a node in the tree:
            tree :== {char: [count, tree] or {None: None} when leaf
        where count is the number of leafs in the sub tree.
        """
        def insert(letters, tree):
            if letters:
                key = letters[0]
                if key in tree:
                    # add tail to sub tree
                    value = tree[key]
                    subtree = value[1]
                    if insert(letters[1:], subtree):
                        value[0] += 1 # increase count
                        return True
                else:
                    # insert into new sub tree
                    subtree = {}
                    insert(letters[1:], subtree)
                    tree[key] = [1, subtree]
                    return True
            elif not None in tree:
                # end of word
                tree[None] = None
                return True

        # build_tree
        tree = {}
        for name in names:
            insert(name, tree)
        return tree

    def remove_one(tree):
        """Remove one leaf from the largest child node in the tree."""
        c = 0 # longest count
        chars = [] # candidate chars to remove
        keys = tree.keys()
        keys.sort()
        # search candidate chars to remove
        for key in keys:
            if tree[key]:
                count = tree[key][0]
                if count > c:
                    c = count
                    chars = [key]
                elif count == c:
                    chars.append(key)
        # remove
        char = None
        if chars:
            # look for highest-valued punctuation
            for c in reversed(chars):
                if c in string.punctuation:
                    char = c
                    break
            else:
                # remove middle char
                char = chars[len(chars) // 2]
        if char is None:
            del tree[None]
        else:
            remove_one(tree[char][1]) # subtree
            tree[char][0] -= 1
            if not tree[char][0]:
                del tree[char]

    def size_of(tree):
        """Return the number of leafs in the tree"""
        n = 0
        for value in tree.itervalues():
            if value:
                n += value[0]
        return n

    def get_names(tree, letters='', buf=None):
        """Return a list with names based on Huffman tree"""
        if buf is None:
            buf=[]
        for key, value in tree.iteritems():
            if key is None:
                buf.append(letters)
            else:
                subtree = value[1]
                get_names(subtree, letters+key, buf)
        return buf

    # reduce_names
    tree = build_tree(names)
    while size_of(tree) > keep:
        remove_one(tree)
    return get_names(tree)
