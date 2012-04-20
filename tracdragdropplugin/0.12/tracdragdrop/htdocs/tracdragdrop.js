jQuery(document).ready(function($) {
    var methodsHTML5 = {
        setup: function() {
            var xhr = new XMLHttpRequest();
            return !!xhr.upload;
        },
        createXMLHttpRequest: function(options) {
            var uploadProgress = options.uploadProgress;
            var headers = options.headers || {};
            var opts = $.extend({}, options);
            var complete = function() {
                xhr.upload.removeEventListener("progress", uploadProgress, false);
            };
            opts.type = 'POST';
            opts.dataType = 'text';
            opts.processData = false;
            opts.contentType = 'application/octet-stream';
            opts.beforeSend = function(xhr, settings) {
                xhr.upload.addEventListener("progress", uploadProgress, false);
                for (var name in headers) {
                    xhr.setRequestHeader(name, headers[name]);
                }
            };
            delete opts.headers;
            delete opts.uploadProgress;
            $.ajax(opts);
        },
        getDataTransfer: function(event) {
            return event.originalEvent.dataTransfer;
        }
    };

    var urls = null;
    var methods = null;
    if (!initialize()) {
        return;
    }

    var indicator =
        $('<div id="tracdragdrop_indicator" />')
        .text(_("Enabled drag-and-drop attachments"))
        .appendTo(document.body);
    var queueFiles = [];
    var countFiles = 0;
    var target = $('body');
    target
        .bind('dragenter', dragenter)
        .bind('dragleave', dragleave)
        .bind('dragover', dragover)
        .bind('drop', drop);
    var notice = null;
    var notice_entire_text = null;
    var notice_entire_progress = null;
    var notice_curr_text = null;
    var notice_curr_progress = null;
    var dragging = [];

    function dragenter(event) {
        var transfer = event.originalEvent.dataTransfer;
        var types = transfer.types;
        var length = types.length;
        var dragFiles = false;
        var i;
        for (i = 0; i < length; i++) {
            if (types[i] == 'Files') {
                dragFiles = true;
                break;
            }
        }
        if (dragFiles === true) {
            if (dragging.length === 0) {
                indicator.addClass('active');
            }
            dragging.push(event.target);
            dragging = $.unique(dragging);
            return false;
        }
    }
    function dragleave(event) {
        dragging = $.grep(dragging, function(value, index) { return value != event.target });
        if (dragging.length === 0) {
            indicator.removeClass('active');
        }
        return false;
    }
    function dragover(event) {
        return false;
    }
    function drop(event) {
        dragging = [];
        indicator.removeClass('active');
        var transfer = methods.getDataTransfer(event);
        var files = transfer.files;
        var length = files.length;
        if (length == 0) {
            return;
        }
        if (!confirm(_("Are you sure you want to attach files?"))) {
            return;
        }
        for (var i = 0; i < length; i++) {
            queueFiles.push(files[i]);
        }
        countFiles += length;
        if (notice === null) {
            startUpload();
        }
        return false;
    }
    function startUpload() {
        var file = null;
        var filename = null;
        notice = $('<div id="tracdragdrop_notice" />')
        notice_entire_text = $('<div class="message" />').appendTo(notice).html('&nbsp;');
        notice_entire_progress = $('<div class="progress"><span></span></div>').appendTo(notice).find('span');
        notice_curr_text = $('<div class="message" />').appendTo(notice).html('&nbsp;');
        notice_curr_progress = $('<div class="progress"><span></span></div>').appendTo(notice).find('span');
        notice.appendTo(document.body);
        startReader();

        function startReader() {
            file = queueFiles.shift();
            filename = $.trim((file.name || '').replace(/[\x00-\x1f]/g, ''));
            startSendContents(file);
        }
        function nextFile() {
            if (queueFiles.length === 0) {
                endUpload();
            }
            else {
                startReader();
            }
        }
        function startSendContents(contents) {
            methods.createXMLHttpRequest({
                url: urls['tracdragdrop.new'],
                data: contents,
                headers: {'X-TracDragDrop-Filename': filename},
                uploadProgress: uploadProgress, success: uploadSuccess, error: uploadError });
        }
        function showProgress(percentage) {
            var value = percentage + '%';
            var n = countFiles - queueFiles.length - 1;
            notice_curr_progress.css('width', value);
            notice_curr_text.text(value);
            notice_entire_progress.css('width',
                Math.round((n * 100 + percentage) / countFiles) + '%');
            notice_entire_text.text((n + (percentage === 100 ? 1 : 0)) + ' / ' + countFiles);
        }
        function uploadProgress(event) {
            if (event.lengthComputable) {
                showProgress(Math.round((event.loaded * 100) / event.total));
            }
        }
        function uploadSuccess(data, textStatus, xhr) {
            showProgress(100);
            nextFile();
        }
        function uploadError(xhr, textStatus, errorThrown) {
            var filename = file.name;
            var message = xhr.responseText;
            setTimeout(function() { alert(filename + ': ' + message) }, 0);
            nextFile();
        }
    }
    function endUpload() {
        notice_entire_text = null;
        notice_entire_progress = null;
        notice_curr_text = null;
        notice_curr_progress = null;
        if (notice) {
            var notice_ = notice;
            function timeout() {
                notice_.animate(
                    { top: '-=' + notice_.height() },
                    250,
                    function() { notice_.remove() });
            }
            setTimeout(timeout, 750);
        }
        notice = null;
        countFiles = 0;
        if (!/[?&]action=edit(?:&|$)/.test(location)) {
            $.ajax({
                type: 'POST', dataType: 'text', url: urls['tracdragdrop.view'],
                success: function(data, textStatus, xhr) {
                    var attachments = $('#attachments');
                    if (attachments.size() > 0) {
                        data = $('<div />').html(data);
                        var elements;
                        if (elements = data.find('dl.attachments'), elements.size() !== 0) {
                            var container = attachments.find('dl.attachments');
                            if (container.size() !== 0) {
                                container.replaceWith(elements);
                            }
                            else {
                                $('form#attachfile').before(elements);
                            }
                        }
                        else if (elements = data.find('ul'), elements.size() !== 0) {
                            var container = attachments.find('ul');
                            if (container.size() !== 0) {
                                container.replaceWith(elements);
                            }
                            else {
                                attachments.replaceWith(data.find('div#attachments'));
                            }
                        }
                    }
                }
            });
        }
    }
    function getUrls() {
        var urls = {};
        var head = document.getElementsByTagName('head')[0];
        var links = head.getElementsByTagName('link');
        var length = links.length;
        for (var i = 0; i < length; i++) {
            var link = links[i];
            var rel = link.getAttribute('rel');
            var href = link.getAttribute('href');
            if (href === null) {
                continue;
            }
            switch (rel) {
            case 'tracdragdrop.view':
            case 'tracdragdrop.new':
                urls[rel] = href;
                break;
            }
        }
        return urls['tracdragdrop.view'] && urls['tracdragdrop.new'] ? urls : null;
    }
    function showReaderError(file, e) {
        var text;
        switch (e.code) {
        case e.NOT_FOUND_ERR:
            text = babel.format(_("%(name)s is not found."),
                                {name: file.name});
            break;
        case e.SECURITY_ERR:
            text = babel.format(_("%(name)s could not be accessed for security reasons."),
                                {name: file.name});
            break;
        case e.NOT_READABLE_ERR:
            text = babel.format(_("%(name)s could not be read."),
                                {name: file.name});
            break;
        default:
            text = e.toString();
            break;
        }
        alert(text);
    }
    function initialize() {
        urls = getUrls();
        if (urls) {
            var list = [ methodsHTML5 ];
            var length = list.length;
            for (var i = 0; i < length; i++) {
                try {
                    var m = list[i];
                    if (m.setup.call(m)) {
                        methods = m;
                        return true;
                    }
                }
                catch (e) { }
            }
        }
        return false;   // not available
    }
});
