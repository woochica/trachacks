jQuery(document).ready(function($) {
    if (!window.overlayview)
        return;

    function loadStyleSheet(href, type) {
        var links = $('link[rel="stylesheet"]').filter(':not([disabled])');
        links = $.grep(links, function(link) {
            return link.getAttribute('href') === href;
        });
        if (links.length === 0) {
            $.loadStyleSheet(href, type);
        }
    }

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
    }

    window.overlayview.loadStyleSheet = loadStyleSheet;
    var baseurl = window.overlayview.baseurl;
    var attachment_url = baseurl + 'attachment/';
    var raw_attachment_url = baseurl + 'raw-attachment/';
    var basic_options = {
        opacity: 0.9, transition: 'none', speed: 200, width: '92%',
        maxWidth: '92%', maxHeight: '92%', onComplete: onComplete};
    var attachments = $('#attachments').get(0);
    var imageRegexp = /\.(?:png|jpe?g|gif|bmp)(?:[#?].*)?$/i;

    function rawlink() {
        var self = $(this);
        var href = self.attr('href');
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
            if (imageRegexp.test(href)) {
                href = raw_attachment_url +
                       href.substring(attachment_url.length);
                options.transition = 'elastic';
                options.photo = true;
                options.width = false;
            }
            else {
                href = baseurl + 'overlayview/' +
                       href.substring(baseurl.length)
                           .replace(/\.([A-Za-z0-9]+)$/, '%2e$1');
            }
            options.href = href;
            var title = anchor.clone();
            title.children('em').contents().appendTo(title);
            title.remove('em');
            options.title = $('<span/>')
                            .append(title, self.clone())
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
            var rawlink = raw_attachment_url +
                          href.substring(attachment_url.length);
            if (imageRegexp.test(href)) {
                options.href = rawlink;
                options.transition = 'elastic';
                options.photo = true;
                options.width = false;
            }
            else {
                options.href = baseurl + 'overlayview/' +
                               href.substring(baseurl.length)
                                   .replace(/\.([A-Za-z0-9]+)$/, '%2e$1');
            }
            rawlink = $('<a/>').addClass('overlayview-rawlink')
                               .attr('href', rawlink)
                               .text('\u200b');
            options.title = $('<span/>')
                            .append(parent, ': ', filename, rawlink)
                            .html();
            anchor.attr('data-colorbox-title', options.title);
            anchor.colorbox(options);
        }
    }

    function imageMacro() {
        var options = $.extend({}, basic_options);
        var image = $(this);
        var href = image.attr('src');
        options.href = href;
        options.transition = 'elastic';
        options.initialWidth = this.width;
        options.initialHeight = this.height;
        options.photo = true;
        options.width = false;
        var filename = href.substring(href.lastIndexOf('/') + 1);
        filename = decodeURIComponent(filename);
        var anchor = $('<a />').attr('href', image.parent().attr('href'))
                               .text(filename);
        if (href.substring(0, raw_attachment_url.length)
            === raw_attachment_url)
        {
            anchor.append($('<a/>').addClass('overlayview-rawlink')
                                   .attr('href', href)
                                   .text('\u200b'));
        }
        options.title = $('<span />').append(anchor).html();
        image.attr('data-colorbox-title', options.title);
        image.colorbox(options);
    }

    $('#content a.trac-rawlink').each(rawlink);
    $('.timeline#content dt.attachment a').each(timeline);
    $('#content .searchable a > img').each(imageMacro);
});
