# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Alec Thomas <alec@swapoff.org>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.resource import Resource, get_resource_url, render_resource_link
from trac.wiki.macros import WikiMacroBase
from trac.util.compat import sorted, set
from tractags.api import TagSystem
from genshi.builder import tag as builder


def render_cloud(req, cloud, rel='tag'):
    """Render a dictionary of {object: (count, href)}."""
    min_px = 10.0
    max_px = 30.0
    scale = 1.0

    size_lut = dict([(c, float(i)) for i, c in
                     enumerate(sorted(set([r[0] for r in cloud.values()])))])
    if size_lut:
        scale = (max_px - min_px) / len(size_lut)

    ul = builder.ul(class_='tagcloud')
    last = len(cloud) - 1
    for i, (tag, (count, href)) in enumerate(sorted(cloud.iteritems())):
        li = builder.li()
        if i == last:
            li(class_='last')
        li(builder.a(
            tag, rel=rel, title='%i' % count, href=href,
            style='font-size: %ipx' % (min_px + int(size_lut[count] * scale)),
            ))
        ul(li)
    return ul


class TagCloudMacro(WikiMacroBase):
    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_result = TagSystem(self.env).query(req, content)
        all_tags = {}
        # Find tag counts
        for resource, tags in query_result:
            for tag in tags:
                try:
                    all_tags[tag] += 1
                except KeyError:
                    all_tags[tag] = 1

        for tag, count in all_tags.items():
            all_tags[tag] = \
                (count, get_resource_url(self.env, Resource('tag', tag), req.href))
        return render_cloud(req, all_tags)



class ListTaggedMacro(WikiMacroBase):
    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_result = TagSystem(self.env).query(req, content)

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        ul = builder.ul(class_='taglist')
        for resource, tags in sorted(query_result, key=lambda r: r[0].id):
            tags = sorted(tags)
            if tags:
                rendered_tags = [
                    link(resource('tag', tag))
                    for tag in tags
                    ]
                li = builder.li(link(resource), ' (', rendered_tags[0],
                                [(' ', tag) for tag in rendered_tags[1:]],
                                ')')
            else:
                li = builder.li(link(resource))
            ul(li, '\n')
        return ul
