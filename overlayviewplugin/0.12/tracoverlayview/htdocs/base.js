jQuery(document).ready(function($) {
    if (!window.overlayview)
        return;

    window.overlayview.loadStyleSheet = function(href, type) {
        var links = $('link[rel="stylesheet"]').filter(':not([disabled])');
        links = $.grep(links, function(link) {
            return link.getAttribute('href') === href;
        });
        if (links.length === 0) {
            $.loadStyleSheet(href, type);
        }
    };

    function onComplete() {
        var element = $.colorbox.element();
        var loaded = $('#cboxLoadedContent');
        var target;
        target = loaded.children('div.image-file').children('img');
        if (target.size() === 1) {
            target.each(function() {
                var url = target.attr('src');
                var options = $.extend({}, basic_options, {
                    title: element.attr('data-colorbox-title'),
                    width: false,
                    href: url,
                    photo: true,
                    open: true
                });
                element.colorbox(options);
            });
            return;
        }
        target = loaded.find('table.code thead tr th.lineno');
        if (target.size() === 1) {
            target.each(function() {
                var url = element.attr('href');
                var change = function() {
                    var anchor = $(this).attr('href');
                    if (anchor.substring(0, 2) === '#L') {
                        $(this).attr('href', url + anchor);
                    }
                };
                loaded.find('table.code tbody tr th[id]').each(function() {
                    this.removeAttribute('id');
                    var anchor = $(this).children('a[href]');
                    if (anchor.size() === 1) {
                        anchor.each(change);
                    }
                });
            });
            return;
        }
    };
    var baseurl = window.overlayview.baseurl;
    var attachment_url = baseurl + 'attachment/';
    var basic_options = {
        opacity: 0.9, transition: 'none', width: '92%', maxWidth: '92%',
        maxHeight: '92%', onComplete: onComplete};
    var attachments = $('#attachments').get(0);
    function rawlink() {
        var self = $(this);
        var anchor = self.prev('a');
        if (anchor.size() === 0) {
            anchor = self.parent('.noprint').prev('a.attachment');
        }
        if (anchor.size() === 0) {
            return;
        }
        if (attachments && $.contains(attachments, this)) {
            anchor.attr('rel', 'colorbox-attachments');
        }
        var href = anchor.attr('href');
        if (href.indexOf(attachment_url) === 0) {
            var options = $.extend({}, basic_options);
            options.href = baseurl + 'overlayview/' +
                           href.substring(baseurl.length)
                               .replace(/\.([A-Za-z0-9]+)$/, '%2e$1');
            var title = anchor.clone();
            title.children('em').contents().appendTo(title);
            title.remove('em');
            options.title = $('<span/>').append(title)
                                        .append(self.clone())
                                        .html();
            anchor.attr('data-colorbox-title', options.title);
            anchor.colorbox(options);
        }
    }
    function timeline() {
        var anchor = $(this);
        var href = anchor.attr('href');
        if (href.indexOf(attachment_url) === 0) {
            var options = $.extend({}, basic_options);
            var em = anchor.children('em');
            var parent_href = baseurl + href.substring(attachment_url.length)
                                            .replace(/\/[^\/]*$/, '');
            var parent = $('<a/>').attr('href', parent_href)
                                  .text($(em.get(1)).text());
            var filename = $('<a/>').attr('href', href)
                                    .text(em.first().text());
            options.href = baseurl + 'overlayview/' +
                           href.substring(baseurl.length)
                               .replace(/\.([A-Za-z0-9]+)$/, '%2e$1');
            var rawlink = baseurl + 'raw-attachment/' +
                          href.substring(attachment_url.length);
            rawlink = $('<a/>').addClass('overlayview-rawlink')
                               .attr('href', rawlink)
                               .text('\u200b');
            options.title = $('<span/>').append(parent)
                                        .append(': ')
                                        .append(filename)
                                        .append(rawlink)
                                        .html();
            anchor.attr('data-colorbox-title', options.title);
            anchor.colorbox(options);
        }
    }
    $('#content a.trac-rawlink').each(rawlink);
    $('.timeline#content dt.attachment a').each(timeline);
});
