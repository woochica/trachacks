# -*- coding: utf-8 -*-

from genshi.builder import tag
from genshi.filters import Transformer

from trac.core import Component, implements
from trac.config import ListOption, BoolOption, Option
from trac.web.api import ITemplateStreamFilter
from trac.util.compat import partial
from trac.util.text import unicode_urlencode

__all__ = ['SharingButtonsFilterModule']

class SharingButtonsFilterModule(Component):
    implements(ITemplateStreamFilter)

    _buttons = ListOption('sharing-buttons', 'buttons', 'twitter,facebook')
    _buttons_class = Option('sharing-buttons', 'buttons_class', '')
    _buttons_style = Option('sharing-buttons', 'buttons_style', '')
    _transform_xpath = Option('sharing-buttons', 'transform_xpath', '')
    _transform_method = Option('sharing-buttons', 'transform_method', '')

    _default_settings = {
        'buttons_class': 'noprint sharing-buttons',
        'buttons_style': 'margin-left:6px',
        'transform_xpath': '//div[@id="content"]//h1',
        'transform_method': 'append',
        'buttons_class.wiki_view': 'noprint sharing-buttons',
        'buttons_style.wiki_view': 'margin-left:6px',
        'transform_xpath.wiki_view': '//div[@id="pagepath"]',
        'transform_method.wiki_view': 'append',
    }

    _twitter_data_count = Option('sharing-buttons', 'twitter.data-count',
        'horizon')

    _facebook_width = Option('sharing-buttons', 'facebook.width', '112')
    _facebook_font = Option('sharing-buttons', 'facebook.font', 'arial')
    _facebook_layout = Option('sharing-buttons', 'facebook.layout',
        'button_count')

    _hatena_bookmark_layout = Option('sharing-buttons',
        'hatena-bookmark.layout', 'standard')

    _wiki_enabled = BoolOption('sharing-buttons', 'wiki_enabled', 'true')
    _milestone_enabled = BoolOption('sharing-buttons', 'milestone_enabled',
        'true')
    _browser_enabled = BoolOption('sharing-buttons', 'browser_enabled', 'true')
    _report_enabled = BoolOption('sharing-buttons', 'report_enabled', 'true')
    _ticket_enabled = BoolOption('sharing-buttons', 'ticket_enabled', 'true')

    def filter_stream(self, req, method, filename, stream, data):
        url = None

        if req.method != 'GET':
            return stream

        elif filename == 'ticket.html':
            model = data.get('ticket')
            if model and model.exists and self._ticket_enabled:
                return self._transform(stream, req, filename, url)

        elif filename in ('wiki_view.html', 'wiki_diff.html'):
            model = data.get('page')
            if model and model.exists and self._wiki_enabled:
                if req.args.get('action', 'view') == 'view' \
                        and not req.args.get('page'):
                    url = req.abs_href.wiki(model.name)
                return self._transform(stream, req, filename, url)

        elif filename == 'milestone_view.html':
            model = data.get('milestone')
            if model and model.exists and self._milestone_enabled:
                return self._transform(stream, req, filename, url)

        elif filename == 'roadmap.html':
            if self._milestone_enabled:
                return self._transform(stream, req, filename, url)

        elif filename in ('dir_entries.html', 'browser.html',
                          'changeset.html', 'diff_form.html',
                          'revisionlog.html'):
            if self._browser_enabled:
                return self._transform(stream, req, filename, url)

        elif filename == 'report_view.html':
            if self._report_enabled:
                return self._transform(stream, req, filename, url)

        return stream

    def _get_config(self, name, filename):
        key = '%s.%s' % (name, filename)
        val = self.config.get('sharing-buttons', key)
        if not val and key in self._default_settings:
            return self._default_settings[key]
        val = self.config.get('sharing-buttons', name)
        return val or self._default_settings[name]

    def _transform(self, stream, req, filename, url):
        filename = filename.rstrip('.html')
        xpath = self._get_config('transform_xpath', filename)
        method = self._get_config('transform_method', filename)
        class_ = self._get_config('buttons_class', filename)
        style = self._get_config('buttons_style', filename)

        if method not in ('after', 'before', 'append', 'prepend'):
            return stream

        locale = req.locale and str(req.locale)
        transformer = Transformer(xpath)
        kwargs = {'class_': class_ or None, 'style': style or None}
        create = partial(self._create_buttons, url, locale, kwargs)
        return stream | getattr(transformer, method)(create)

    def _create_buttons(self, url, locale, kwargs):
        args = []
        for button in self._buttons:
            if button == 'twitter':
                args.extend(self._create_twitter_button(url, locale))
            elif button == 'facebook':
                args.extend(self._create_facebook_button(url, locale))
            elif button == 'hatena-bookmark':
                args.extend(self._create_hatena_bookmark_button(url, locale))
        return tag.span(*args, **kwargs)

    def _create_twitter_button(self, url, locale):
        return [
            tag.a('Tweet',
                  href='//twitter.com/share',
                  class_='twitter-share-button',
                  data_url=url, data_counturl=url,
                  data_lang=locale or None,
                  data_count=self._twitter_data_count),
            tag.script(type='text/javascript',
                       src='//platform.twitter.com/widgets.js'),
        ]

    def _create_facebook_button(self, url, locale):
        width = self._facebook_width
        font = self._facebook_font
        layout = self._facebook_layout

        params = {'width': width, 'font': font, 'layout': layout,
                  'send': 'false', 'action': 'like'}
        if url:
            params['url'] = url
        if locale:
            params['locale'] = locale
        src = '//www.facebook.com/plugins/like.php?' + unicode_urlencode(params)
        style = 'border:none;overflow:hidden;width:%(width)spx;height:21px' \
                % {'width': width}
        return [
            tag.iframe(src=src, scrolling='no', frameborder='0', style=style,
                       allowTransparency='true'),
        ]

    def _create_hatena_bookmark_button(self, url, locale):
        href = '//b.hatena.ne.jp/entry/'
        if url:
            href += url.replace('#', '%23')
        return [
            tag.a(tag.img(src='//b.st-hatena.com/images/entry-button/button-only.gif',
                          alt=u'このエントリーをはてなブックマークに追加',
                          width='20', height='20', style='border:none'),
                  href=href, class_='hatena-bookmark-button',
                  data_hatena_bookmark_layout=self._hatena_bookmark_layout,
                  title=u'このエントリーをはてなブックマークに追加'),
            tag.script(type='text/javascript', charset='utf-8', async='async',
                       src='//b.st-hatena.com/js/bookmark_button_wo_al.js'),
        ]
