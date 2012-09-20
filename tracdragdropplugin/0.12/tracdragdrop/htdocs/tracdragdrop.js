jQuery(document).ready(function($) {
    /* From 0.12-stable/trac/htdocs/js/babel.js */
    var babel = window.babel;
    if (babel.format('%(arg)d%%', {arg: 1}) !== '1%') {
        babel = $.extend({}, babel);
        babel.format = (function() {
            var formatRegex = /%(?:(?:\(([^\)]+)\))?([disr])|%)/g;
            var babel = {};
            return function() {
                var arg, string = arguments[0], idx = 0;
                if (arguments.length == 1)
                    return string;
                if (arguments.length == 2 && typeof arguments[1] == 'object')
                    arg = arguments[1];
                else {
                    arg = [];
                    for (var i = 1, n = arguments.length; i != n; ++i)
                        arg[i - 1] = arguments[i];
                }
                return string.replace(formatRegex, function(all, name, type) {
                    if (all == '%%')
                        return '%';
                    var value = arg[name || idx++];
                    return (type == 'i' || type == 'd') ? +value : value; 
                });
            };
        })();
    }
    var _ = (function() {
        var tx = babel.Translations;
        if (tx && tx.get) {
            var rv = tx.get('tracdragdrop-js');
            return function() {
                return rv.gettext.apply(rv, arguments);
            };
        }
        return window.gettext;
    })();

    if (window.Clipboard || false) {
        $('#content').delegate('a.trac-rawlink', 'dragstart', function(event) {
            var transfer = event.originalEvent.dataTransfer || false;
            if (!transfer || transfer.constructor != Clipboard) {
                return;
            }
            var href = this.href;
            var name = href.substring(href.lastIndexOf('/') + 1);
            name = decodeURIComponent(name).replace(/:/g, '_');
            var data = ['application/octet-stream', name, href].join(':');
            try {
                transfer.setData('DownloadURL', data);
            }
            catch (e) { }
        });
    }
    var tracdragdrop = window._tracdragdrop || undefined;
    var form_token = window.form_token || undefined;
    if (!tracdragdrop || !form_token) {
        return;
    }
    var attachments = $('div#content > div#attachments');
    var attachfile = $('form#attachfile');
    var viewpage = attachfile.size() !== 0;
    var xhrHasUpload = window.XMLHttpRequest &&
                       !!(new XMLHttpRequest()).upload;
    var hasFileReader = !!window.FileReader;
    var hasFormData = !!window.FormData;
    var hasDragAndDrop = xhrHasUpload && hasFileReader;
    var toBlob = (function() {
        try {
            new Blob(['data'], {type: 'application/octet-stream'});
            return function(parts, mimetype) {
                return new Blob(parts, {type: mimetype});
            };
        }
        catch (e) { }
        var BlobBuilder = window.BlobBuilder || window.WebKitBlobBuilder ||
                          window.MozBlobBuilder || window.MSBlobBuilder ||
                          undefined;
        if (BlobBuilder) {
            return function(parts, mimetype) {
                var builder = new BlobBuilder();
                var length = parts.length;
                for (var i = 0; i < length; i++) {
                    builder.append(parts[i].buffer);
                }
                return builder.getBlob(mimetype);
            };
        }
        return undefined;
    })();
    var containers = {list: null, queue: null, dropdown: null};
    var queueItems = [];
    var queueCount = 0;
    var compact = attachments.find('form#attachfile').size() === 0 &&
                  attachments.find('div > dl.attachments').size() === 0;

    function ajaxUpload(options) {
        var opts = $.extend({}, options);
        var upload = xhrHasUpload ? opts.upload : {};
        var headers = opts.headers || {};
        var data = opts.data;
        var isFormData = hasFormData && data instanceof FormData;
        var xhr;
        opts.xhr = function() {
            xhr = $.ajaxSettings.xhr();
            for (var type in upload) {
                xhr.upload.addEventListener(type, upload[type], false);
            }
            return xhr;
        };
        opts.type = 'POST';
        opts.dataType = 'text';
        opts.processData = false;
        opts.beforeSend = function(xhr, settings) {
            for (var name in headers) {
                xhr.setRequestHeader(name, headers[name]);
            }
            if (isFormData) {
                settings.data = data;
            }
        };
        opts.complete = function(jqxhr, status) {
            for (var type in upload) {
                xhr.upload.removeEventListener(type, upload[type], false);
            }
            xhr = undefined;
        };
        if (isFormData) {
            delete opts.data;
            opts.contentType = false;
        }
        else {
            opts.contentType = 'application/octet-stream';
        }
        delete opts.headers;
        delete opts.progress;
        return $.ajax(opts);
    }

    function textNode(val, d) {
        return (d || document).createTextNode(val);
    }

    function generateTracLink(val) {
        var text = 'attachment:' + val;
        if (!/[ \t\f\v"']/.test(val))
            return text;
        if (!/"/.exec(val))
            return 'attachment:"' + val + '"';
        if (!/'/.exec(val))
            return "attachment:'" + val + "'";
        return text; // XXX maybe corrupted link
    }

    function generateImageMacro(val) {
        return '[[Image(' + val + ')]]';
    }

    function refreshAttachmentsList(src) {
        src = $('<div />').html(src);
        var list = containers.list;
        var srcList = src.find(compact ? 'ul' : 'dl.attachments');
        var n = srcList.children(compact ? 'li' : 'dt').length;
        if (list !== null) {
            containers.dropdown.appendTo(document.body);
            list.empty().append(srcList.contents());
        }
        else {
            if (compact) {
                attachments.prepend(src.find('div#attachments').contents())
                           .children('.foldable')
                           .enableFolding(true, viewpage);
            }
            else {
                containers.queue.before(srcList);
            }
            setContainerList(srcList);
        }
        var count = attachments.find('span.trac-count');
        var countText = count.text();
        if (/[0-9]/.test(countText)) {
            count.text(countText.replace(/[0-9]+/, n));
        }
        attachments.removeClass('collapsed');
    }

    function generateFilenamePrefix(now) {
        function pad0(val, size) {
            var pad;
            switch (size) {
                case 2: pad = '00'; break;
                case 4: pad = '0000'; break;
            }
            return (pad + val).slice(-size);
        }
        now = now || new Date();
        now = {year: now.getFullYear(), month: now.getMonth() + 1,
               date: now.getDate(), hours: now.getHours(),
               minutes: now.getMinutes(), seconds: now.getSeconds()};
        return [
            'image-',
            pad0(now.year, 4), pad0(now.month, 2), pad0(now.date, 2),
            '-',
            pad0(now.hours, 2), pad0(now.minutes, 2), pad0(now.seconds, 2),
        ].join('');
    }

    function generateFilename(prefix, mimetype, n) {
        var suffix;
        switch (mimetype) {
        case 'image/png':
        case 'image/jpeg':
        case 'image/gif':
            suffix = '.' + mimetype.substring(6);
            break;
        default:
            suffix = mimetype.substring(0, 6) === 'image/'
                   ? '.' + mimetype.substring(6)
                   : '.dat';
            break;
        }
        return n === undefined ? (prefix + suffix)
                               : (prefix + '-' + n + suffix);
    }

    function createPasteArea(form) {
        var message = _("Paste an image to attach");
        var events = {};
        events.mouseenter = function() { $(this).focus() };
        events.focus = function() {
            this.setAttribute('contenteditable', 'true');
            $(this).empty();
        };
        events.blur = function() {
            $(this).empty();
            this.removeAttribute('contenteditable');
            this.blur();
        };
        events.keyup = function() { $(this).empty() };
        events.keypress = function(event) {
            return event.ctrlKey === true || event.metaKey === true;
        };
        events.paste = function(event) {
            var editable = $(this);
            var prefix = generateFilenamePrefix();

            if (event.originalEvent.clipboardData &&
                event.originalEvent.clipboardData.items)
            {
                var images = [];
                $.each(event.originalEvent.clipboardData.items, function() {
                    if (/^image\//i.test(this.type)) {
                        images.push(this.getAsFile());
                    }
                });
                switch (images.length) {
                case 0:
                    alert(_("No available image on your clipboard"));
                    return false;
                case 1:
                    var filename = generateFilename(prefix, images[0].type);
                    prepareUploadItem(images[0], {filename: filename});
                    break;
                default:
                    $.each(images, function(idx, image) {
                        var filename = generateFilename(prefix, image.type,
                                                        idx + 1);
                        prepareUploadItem(image, {filename: filename});
                    });
                    break;
                }
                startUpload();
                return false;
            }

            setTimeout(function() {
                var element = editable.children().filter(':not(br)');
                editable.empty();
                if (element.size() !== 1 ||
                    element.get(0).nodeName.toLowerCase() !== 'img')
                {
                    alert(_("No available image on your clipboard"));
                    return;
                }
                var filename = prefix + '.png';
                var image = element.get(0);
                image.removeAttribute('width');
                image.removeAttribute('height');
                if (image.width !== 0 && image.height !== 0) {
                    prepareUploadImageUsingCanvas(image, filename);
                    return;
                }
                var events = {};
                events.load = function() {
                    element.unbind();
                    element = image = undefined;
                    prepareUploadImageUsingCanvas(this, filename);
                };
                events.error = function(e) {
                    element.unbind();
                    element = image = undefined;
                    alert(babel.format(
                        _("Cannot load an image from '%(src)s'."),
                        {src: this.src}));
                };
                element.bind(events);
            }, 1);
        };
        var editable = $('<div />')
            .addClass('tracdragdrop-paste beautytips')
            .attr('title',
                  _("You can attach an image from your clipboard directly " +
                    "with CTRL-V or \"Paste\" on the context menu."))
            .attr('data', message)
            .bind(events);
        form.append($('<div />').append(editable));
        editable.css({width: editable.width() + 'px',
                      height: editable.height() + 'px'});
    }

    function prepareUploadImageUsingCanvas(image, filename) {
        var canvas = image.ownerDocument.createElement('canvas');
        canvas.width = image.width;
        canvas.height = image.height;
        var context = canvas.getContext('2d');
        context.drawImage(image, 0, 0);
        var data;
        try {
            if (canvas.toBlob) {
                canvas.toBlob(function(data) {
                    prepareUploadItem(data, {filename: filename});
                    startUpload();
                });
                return;
            }
            data = canvas.getAsFile ? canvas.getAsFile(filename)
                                    : canvas.mozGetAsFile(filename);
        }
        catch (e) {
            alert(babel.format(_("Cannot load an image from '%(src)s'."),
                               {src: image.src}));
            return;
        }
        prepareUploadItem(data, {filename: filename});
        startUpload();
    }

    function prepareUploadItem(item, options) {
        options = options || {};
        var key = '#' + ++queueCount;
        var filename = 'filename' in options ? options.filename : item.name;
        var size = 'size' in options ? options.size : item.size;
        var description = 'description' in options ? options.description : '';
        var element, progress, cancel, message, error;
        filename = $.trim(filename).replace(/[\x00-\x1f]/g, '');
        if (xhrHasUpload) {
            progress = $('<span />').addClass('tracdragdrop-progress')
                                    .append($('<div />'));
        }
        cancel = $('<span />').addClass('tracdragdrop-cancel')
                              .text('×');
        message = $('<span />').addClass('tracdragdrop-message');
        element = $(compact ? '<li />' : '<dt />')
                  .attr('data-tracdragdrop-key', key)
                  .append(cancel);
        if (progress !== undefined) {
            element.append(textNode(' '), progress);
        }
        element.append(textNode(' ' + filename), message);
        containers.queue.append(element);
        if (!xhrHasUpload && !hasFileReader) {
            queueItems.push({element: element, message: message, key: key});
            return key;
        }
        if (tracdragdrop.max_size > 0 && size > tracdragdrop.max_size) {
            error = babel.format(
                _("Exceeded maximum allowed file size (%(size)s bytes)"),
                {size: tracdragdrop.max_size});
        }
        else if (size === 0) {
            error = _("Can't upload empty file");
        }
        if (error === undefined) {
            var data = {};
            data.data = item;
            data.filename = filename;
            data.description = description;
            data.size = size;
            data.element = element;
            data.message = message;
            data.xhr = null;
            data.key = key;
            queueItems.push(data);
        }
        else {
            message.text(' \u2013 ' + error);
        }
        return key;
    }

    function cancelUploadItem() {
        var item = $(this);
        var key = item.attr('data-tracdragdrop-key');
        var found = false;
        $.each(queueItems, function(idx, val) {
            if (val.key === key) {
                finishUploadItem(key, _("Canceled"));
                var xhr = val.xhr;
                val.xhr = false;
                val.data = null;
                if (xhr) {
                    xhr.abort();
                }
                found = true;
                return false;
            }
        });
        if (!found) {
            item.remove();
        }
    }

    function uploadItem(entry) {
        function setProgress(rate) {
            var val = rate !== null
                    ? Math.min(rate, 1) * 100
                    : (parseFloat(bar.css('width')) + 10) % 100;
            bar.css('width', val + '%');
            if (rate !== null) {
                loading.text(babel.format(_("Uploaded %(percent)s%%"),
                                          {percent: val.toPrecision(3)}));
            }
        }
        var loading = $('<span />').addClass('tracdragdrop-loading');
        var bar = entry.element.find('.tracdragdrop-progress > div');
        var key = entry.key;
        entry.message.empty().append(loading);
        var options = {};
        options.url = tracdragdrop['new_url'];
        options.headers = {
            'X-TracDragDrop-Filename': encodeURIComponent(entry.filename),
            'X-TracDragDrop-Compact': compact ? '1' : '0'};
        if (xhrHasUpload) {
            var upload = {};
            options.upload = upload;
            upload.progress = function(event) {
                setProgress(event.lengthComputable ? event.loaded / event.total
                                                   : null);
            };
            upload.loadstart = function() { setProgress(0) };
            upload.loadend = function() {
                if (entry.xhr) {
                    setProgress(1);
                }
            };
        }
        else {
            loading.text(_("Uploading..."));
        }
        options.success = function(data, status, xhr) {
            finishUploadItem(key);
            if (data) {
                refreshAttachmentsList(data);
            }
        };
        options.error = function(xhr, status, error) {
            var msg;
            switch (status) {
            case 'timeout':
                msg = _("Timed out");
                break;
            case 'abort':
                msg = _("Aborted");
                break;
            default: // 'error'
                if (xhr) {
                    msg = xhr.responseText;
                    if (/^\s*<(?:!DOCTYPE|\?xml)/.test(msg)) {
                        msg = xhr.statusText + ' (' + xhr.status + ')';
                    }
                }
                else {
                    msg = status;
                }
                break;
            }
            finishUploadItem(key, msg);
        };
        if (entry.description && hasFormData) {
            var data = new FormData();
            data.append('__FORM_TOKEN', form_token);
            data.append('attachment', entry.data, entry.filename);
            data.append('compact', compact ? '1' : '0');
            data.append('description', entry.description);
            options.data = data;
        }
        else {
            options.data = entry.data;
        }
        if (xhrHasUpload) {
            entry.xhr = ajaxUpload(options);
            return;
        }
        var reader = new FileReader();
        var events = {};
        events.loadend = function() {
            for (var name in events) {
                reader.removeEventListener(name, events[name], false);
            }
        };
        events.error = function() {
            options.error(null, reader.error.toString());
        };
        events.load = function() {
            options.data = reader.result;
            entry.xhr = ajaxUpload(options);
        };
        for (var name in events) {
            reader.addEventListener(name, events[name], false);
        }
        entry.xhr = false;
        reader.readAsArrayBuffer(options.data);
    }

    function finishUploadItem(key, message) {
        $.each(queueItems, function(idx, val) {
            if (val.key === key) {
                queueItems.splice(idx, 1);
                var element = val.element;
                if (message === undefined) {
                    element.remove();
                }
                else {
                    element.find('.tracdragdrop-message')
                           .text(' \u2013 ' + message);
                }
                return false;
            }
        });
        nextUploadItem();
    }

    function nextUploadItem() {
        if (queueItems.length === 0) {
            return;
        }
        $.each(queueItems, function(idx, val) {
            if (val.xhr === null) {
                uploadItem(val);
                return false;
            }
        });
    }

    function startUpload() {
        nextUploadItem();
    }

    function prepareAttachForm() {
        var file = $('<input type="file" name="attachment" />')
                   .attr('multiple', 'multiple');
        var legend = $('<legend />').text(_("Add Attachment"));
        var fieldset = $('<fieldset />').append(legend, file);
        var form = $('<form enctype="multipart/form-data" />')
                   .attr({method: 'post', action: tracdragdrop['new_url']})
                   .addClass('tracdragdrop-form')
                   .append(fieldset);
        var queue;
        var hidden = false;
        if (attachfile.size() === 0) {
            queue = $('<ul />').addClass('tracdragdrop-queue');
            attachfile = form.attr('id', 'attachfile');
            attachments.append(queue, form);
        }
        else if (compact) {
            queue = $('<ul />').addClass('tracdragdrop-queue');
            attachfile.submit(function() {
                form.toggle();
                attachfile.find(':submit').blur();
                return false;
            });
            attachments.after(queue, form);
            hidden = true;
        }
        else {
            form.attr('id', 'attachfile');
            attachfile.replaceWith(form);
            attachfile = form;
            queue = $('<dl />').addClass('attachments tracdragdrop-queue');
            form.before(queue);
        }
        containers.queue = queue;
        if (hasDragAndDrop) {
            fieldset.append(textNode(
                ' ' + _("You may use drag and drop here.")));
            if ('onpaste' in document.body) {
                createPasteArea(fieldset);
            }
        }
        if (xhrHasUpload || file.get(0).files && hasFileReader) {
            queue.delegate('dt, li', 'click', cancelUploadItem);
            file.bind('change', function() {
                $.each(this.files, function() { prepareUploadItem(this) });
                this.form.reset();
                startUpload();
            });
        }
        else {
            queue.delegate('dt, li', 'click', function() {
                var item = $(this);
                var key = item.attr('data-tracdragdrop-key');
                var iframe = $('#tracdragdrop-attachfile-iframe');
                if (iframe.attr('data-tracdragdrop-key') === key) {
                    form.get(0).reset();
                    file.attr('disabled', false);
                    iframe.attr('src', 'about:blank'); // cancel upload
                    iframe.remove();
                }
                cancelUploadItem.call(this);
            });
            var token = $('<input type="hidden" name="__FORM_TOKEN" />');
            form.prepend($('<div />').css('display', 'none').append(token));
            file.bind('change', function() {
                token.val(form_token);
                var key;
                var form = $(this.form);
                var iframe = $('<iframe' +
                    ' width="1" height="1" src="about:blank"' +
                    ' id="tracdragdrop-attachfile-iframe"' +
                    ' name="tracdragdrop-attachfile-iframe"' +
                    ' style="display:none"></iframe>');
                iframe.appendTo(form);
                iframe.bind('load', function() {
                    var data = iframe.get(0).contentWindow.document.body;
                    var valid = data.className == 'tracdragdrop-attachments';
                    data = data.innerHTML;
                    form.attr('target', '');
                    form.get(0).reset();
                    iframe.attr('src', 'about:blank'); // stop loading icon
                    iframe.remove();
                    iframe = null;
                    if (valid) {
                        finishUploadItem(key);
                        refreshAttachmentsList(data);
                    }
                    else {
                        var message = $('<div />').html(data).text();
                        finishUploadItem(key, message);
                    }
                    file.attr('disabled', false);
                });
                form.attr('target', iframe.attr('name'));
                form.focus();
                form.submit();
                file.attr('disabled', true);
                var filename = this.value;
                filename = filename.substring(filename.lastIndexOf('\\') + 1);
                filename = filename.substring(filename.lastIndexOf('/') + 1);
                key = prepareUploadItem(null, {filename: filename, size:-1});
                iframe.attr('data-tracdragdrop-key', key);
                $.each(queueItems, function(idx, val) {
                    if (val.key === key) {
                        val.message.empty().append(
                            $('<span />').addClass('tracdragdrop-loading')
                                         .text(_("Uploading...")));
                        return false;
                    }
                });
            });
        }
        if (hidden) {
            form.hide();
        }
    }

    function setContainerList(element) {
        var dropdown, icon, menu, del;
        var fields = {traclink: null, macro: null};
        var stripHostRegexp = new RegExp('^[^:]+://[^/:]+(?::[0-9]+)?');

        function getFilename(rawlink) {
            var name = $(rawlink).attr('href');
            name = name.substring(name.lastIndexOf('/') + 1);
            return decodeURIComponent(name);
        }
        function getUrl(rawlink, action) {
            var url = $(rawlink).attr('href').replace(stripHostRegexp, '');
            var base_url = tracdragdrop.base_url
            var length = (base_url + 'raw-attachment/').length;
            return base_url + 'tracdragdrop/delete/' + url.substring(length);
        }
        function showIcon(item, rawlink) {
            var filename = getFilename(rawlink);
            var vals = {traclink: generateTracLink(filename),
                        macro: generateImageMacro(filename)};
            item.append(dropdown);
            $.each(vals, function(idx, val) { fields[idx].val(val) });
        }

        fields.traclink =
            $('<input type="text" readonly="readonly" size="30" />')
            .click(function() { this.select() });
        fields.macro = fields.traclink.clone(true);
        del = $('<div  />').append($('<strong />').text('\u00d7\u00a0'),
                                   textNode(_("Delete attachment")))
                           .click(function() {
            var item = $(this).parents('dt, li');
            var rawlink = item.find('a.trac-rawlink');
            var filename = getFilename(rawlink);
            var message = babel.format(
                _("Are you sure you want to delete '%(name)s'?"),
                {name: filename});
            if (confirm(message)) {
                var url = getUrl(rawlink, 'delete');
                $.ajax({
                    url: url,
                    type: 'POST',
                    data: '__FORM_TOKEN=' + form_token,
                    success: function() {
                        dropdown.appendTo(document.body);
                        var count = attachments.find('span.trac-count');
                        var countText = count.text();
                        if (/[0-9]/.test(countText)) {
                            var n = item.parent().find(item[0].tagName).length;
                            count.text(countText.replace(/[0-9]+/,
                                                         Math.max(n - 1, 0)));
                        }
                        item.add(item.next('dd')).remove();
                    },
                    error: function(xhr, status, error) {
                        alert(xhr.responseText || status);
                    }
                });
            }
            menu.hide();
        });
        menu = $.htmlFormat([
            '<table>',
            ' <tbody>',
            '  <tr>',
            '   <td>$1</td>',
            '   <td class="tracdragdrop-traclink"></td>',
            '  </tr>',
            '  <tr>',
            '   <td>$2</td>',
            '   <td class="tracdragdrop-macro"></td>',
            '  </tr>',
            '  <tr class="tracdragdrop-menuitem">',
            '   <td colspan="2" class="tracdragdrop-delete"></td>',
            '  </tr>',
            ' </tbody>',
            '</table>'].join(''), _("TracLink"), _("Image macro"));
        menu = $('<div />').addClass('tracdragdrop-menu')
                           .html(menu);
        menu.find('.tracdragdrop-traclink').append(fields.traclink);
        menu.find('.tracdragdrop-macro').append(fields.macro);
        menu.find('.tracdragdrop-delete').append(del);
        menu.hide();
        menu.find('tr').bind('mouseenter', function() {
            $(this).find('input[type=text]').each(function() { this.click() });
        });
        icon = $('<div />')
               .addClass('tracdragdrop-icon')
               .text('\u25bc')
               .bind('click', function() { menu.toggle() });
        dropdown = $('<div />')
                  .addClass('tracdragdrop-dropdown')
                  .append(icon, menu);
        element.delegate('dt, li', 'mouseenter', function() {
            if (menu.css('display') === 'none') {
                var item = $(this);
                showIcon(item, item.children('a.trac-rawlink'));
            }
        });
        element.delegate('dt > a, li > a', 'click', function(event) {
            if (event.which > 1 || !event.altKey) {
                return;
            }
            var self = $(this);
            var rawlink = self.next('a.trac-rawlink');
            if (rawlink.size() === 0) {
                rawlink = self.prev('a.trac-rawlink');
            }
            if (rawlink.size() === 0) {
                return;
            }
            var item = rawlink.parent();
            if ($.contains(item.get(0), dropdown.get(0))) {
                menu.toggle();
            }
            else {
                showIcon(item, rawlink);
                menu.show();
            }
            return false;
        });
        $('html').click(function(event) {
            if (!$.contains(dropdown.get(0), event.target)) {
                menu.hide();
                dropdown.appendTo(document.body);
            }
        });
        dropdown.appendTo(document.body);

        containers.list = element;
        containers.dropdown = dropdown;
    }

    function convertBlobsFromUriList(urilist) {
        var items = [];
        var re = /^data:([^,;]+)((?:;[^;,]*)*),([^\n]*)/;
        $.each(urilist.split(/\n/), function(idx, line) {
            var match = re.exec(line);
            if (!match) {
                return;
            }
            var mimetype = match[1].toLowerCase();
            switch (mimetype) {
            case 'image/png':
            case 'image/jpeg':
            case 'image/gif':
                break;
            default:
                return;
            }
            var attrs = match[2].substring(1);
            var body = match[3];
            $.each(attrs.split(/;/), function(idx, val) {
                switch (val) {
                case 'base64':
                    body = atob(body);
                    break;
                }
            });
            var length = body.length;
            var buffer = new Uint8Array(length);
            for (var i = 0; i < length; i++) {
                buffer[i] = body.charCodeAt(i);
            }
            var blob = toBlob([buffer], mimetype);
            items.push(blob);
        });
        return items;
    }

    function prepareDragEvents() {
        var body = document.body;
        var elements = $('html');
        var mask = $('<div />');
        var indicator = $('<span />').text(_("Drop files to attach"));
        indicator = $('<div />').append(indicator);
        var effect = $('<div />').addClass('tracdragdrop-dropeffect')
                                 .append(mask, indicator)
                                 .hide()
                                 .click(function() { effect.hide() })
                                 .appendTo(body);
        var dragging = undefined;
        var events = {};
        var type;
        events.dragstart = function(event) { dragging = false };
        events.dragend = function(event) { dragging = undefined };
        events.dragenter = function(event) {
            if (dragging === undefined) {
                var transfer = event.originalEvent.dataTransfer;
                var found;
                $.each(transfer.types, function(idx, type) {
                    type = '' + type;
                    switch (type) {
                    case 'Files':
                    case 'application/x-moz-file':
                        found = type;
                        return false;
                    case 'text/uri-list':
                        if (toBlob) {
                            found = type;
                        }
                        break;
                    }
                });
                if (found === undefined) {
                    return;
                }
                dragging = true;
                type = found;
                effect.show();
            }
            return !dragging;
        };
        events.dragleave = function(event) {
            if (dragging === true && event.target === mask.get(0)) {
                dragging = undefined;
                effect.hide();
            }
        };
        events.dragover = function(event) { return !dragging };
        events.drop = function(event) {
            if (dragging !== true) {
                return;
            }
            dragging = undefined;
            effect.hide();
            var items;
            var transfer = event.originalEvent.dataTransfer;
            switch (type) {
            case 'Files':
            case 'application/x-moz-file':
                items = transfer.files;
                $.each(items, function() { prepareUploadItem(this) });
                break;
            case 'text/uri-list':
                var uris = transfer.getData(type);
                var prefix = generateFilenamePrefix();
                items = convertBlobsFromUriList(uris);
                switch (items.length) {
                case 1:
                    var filename = generateFilename(prefix, items[0].type);
                    prepareUploadItem(items[0], {filename: filename});
                    break;
                default:
                    $.each(items, function(idx, item) {
                        var filename = generateFilename(prefix, item.type,
                                                        idx + 1);
                        prepareUploadItem(item, {filename: filename});
                    });
                    break;
                }
                break;
            }
            if (items.length !== 0) {
                startUpload();
            }
            else {
                alert(_("No available image in the dropped data"));
            }
            items = undefined;
            return false;
        };
        elements.bind(events);
    }

    function initialize() {
        if (attachments.size() === 0) {
            return;
        }
        var foldable = attachments.children('.foldable');
        if ($.fn.enableFolding && foldable.size() !== 0) {
            setTimeout(function() {
                if (foldable.children('a').size() === 0) {
                    foldable.enableFolding(true, viewpage);
                }
            }, 10);
        }
        $.each(compact ? ['div > ul', 'ul'] : ['div > dl.attachments'],
               function(idx, val)
        {
            var list = attachments.find(val);
            if (list.size() !== 0) {
                setContainerList($(list.get(0)));
                return false;
            }
        });
        if (tracdragdrop.can_create) {
            prepareAttachForm();
            if (hasDragAndDrop) {
                prepareDragEvents();
            }
        }
    }

    initialize();
});
