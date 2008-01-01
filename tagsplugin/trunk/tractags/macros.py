from trac.resource import Resource, get_resource_url, render_resource_link
from trac.wiki.macros import WikiMacroBase
from trac.util.compat import sorted, set
from tractags.api import TagSystem
from genshi.builder import tag as builder


class TagCloudMacro(WikiMacroBase):
    def expand_macro(self, formatter, name, content):
        req = formatter.req
        query_result = TagSystem(self.env).query(req, content)

        min_px = 10.0
        max_px = 30.0
        all_tags = {}
        scale = 1.0
        # Find tag counts
        for resource, tags in query_result:
            for tag in tags:
                try:
                    all_tags[tag] += 1
                except KeyError:
                    all_tags[tag] = 1

        size_lut = dict([(c, float(i)) for i, c in
                         enumerate(sorted(set(all_tags.values())))])
        if size_lut:
            scale = (max_px - min_px) / len(size_lut)

        ul = builder.ul(class_='tagcloud')
        last = len(all_tags) - 1
        for i, (tag, count) in enumerate(sorted(all_tags.iteritems())):
            li = builder.li()
            if i == last:
                li(class_='last')
            href = get_resource_url(self.env, Resource('tag', tag), req.href)
            li(builder.a(
                tag, rel='tag', title='%i' % count, href=href,
                style='font-size: %ipx' % (min_px + int(size_lut[count] * scale)),
                ))
            ul(li)
        return ul


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
