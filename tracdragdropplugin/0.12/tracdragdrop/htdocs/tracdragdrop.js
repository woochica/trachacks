jQuery(document).ready(function($) {
    var methodsHTML5 = {
        setup: function() {
            new FileReader();
            var xhr = new XMLHttpRequest();
            return xhr.upload && xhr.sendAsBinary ? true : false;
        },
        createXMLHttpRequest: function(options) {
            var uploadProgress = options.uploadProgress || emptyFunction;
            var success = options.success || emptyFunction;
            var error = options.error || emptyFunction;

            var xhr = new XMLHttpRequest();
            xhr.upload.addEventListener("progress", uploadProgress, false);
            xhr.onreadystatechange = function() {
                switch (xhr.readyState) {
                case 4:
                    if (xhr.status >= 200 && xhr.status < 300) {
                        success(xhr.responseText, xhr.statusText, xhr);
                    }
                    else if (xhr.status >= 400 && xhr.status < 600) {
                        error(xhr, xhr.statusText);
                    }
                    xhr.upload.removeEventListener("progress", uploadProgress, false);
                    xhr.onreadystatechange = null;
                    break;
                }
            };
            xhr.open(options.method || 'POST', options.url, options.async || true);
            for (var name in options.headers) {
                xhr.setRequestHeader(name, options.headers[name]);
            }
            xhr.sendAsBinary(options.data);
            return xhr;
        },
        getDataTransfer: function(event) {
            return event.originalEvent.dataTransfer;
        }
    };
    var methodsGears = {
        setup: function() {
            var xhr = google.gears.factory.create('beta.httprequest');
            if (!xhr.upload) {
                return false;
            }
            this.gearsDesktop = google.gears.factory.create('beta.desktop');
            return true;
        },
        gearsDesktop: null,
        createXMLHttpRequest: function(options) {
            var uploadProgress = options.uploadProgress || emptyFunction;
            var success = options.success || emptyFunction;
            var error = options.error || emptyFunction;

            var xhr = google.gears.factory.create('beta.httprequest');
            xhr.upload.onprogress = uploadProgress;
            xhr.onreadystatechange = function() {
                switch (xhr.readyState) {
                case 4:
                    if (xhr.status >= 200 && xhr.status < 300) {
                        success(xhr.responseText, xhr.statusText, xhr);
                    }
                    else if (xhr.status >= 400 && xhr.status < 600) {
                        error(xhr, xhr.statusText);
                    }
                    xhr.upload.onprogress = null;
                    xhr.onreadystatechange = null;
                    break;
                }
            };
            xhr.open(options.method || 'POST', options.url, options.async || true);
            for (var name in options.headers) {
                xhr.setRequestHeader(name, options.headers[name]);
            }
            xhr.send(options.data);
            return xhr;
        },
        getDataTransfer: function(event) {
            return this.gearsDesktop.getDragData(event.originalEvent, 'application/x-gears-files');
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
        var reader = null;
        var xhr = null;
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
            filename = (file.name || '').replace(/"/g, '');
            if (typeof file.blob != 'undefined') {
                startSendContents(file.blob);
                return;
            }
            reader = new FileReader();
            reader.addEventListener('loadend', readerLoadend, false);
            reader.addEventListener('error', readerError, false);
            reader.addEventListener('abort', readerAbort, false);
            try {
                reader.readAsBinaryString(file);
            }
            catch (e) {
                var file_ = file;
                setTimeout(function() { showReaderError(file_, e) }, 10);
                cleanReader();
                nextFile();
            }
        }
        function cleanReader() {
            if (reader !== null) {
                reader.removeEventListener('loadend', readerLoadend, false);
                reader.removeEventListener('error', readerError, false);
                reader.removeEventListener('abort', readerAbort, false);
                reader = null;
            }
        }
        function nextFile() {
            xhr = null;
            if (queueFiles.length === 0) {
                endUpload();
            }
            else {
                startReader();
            }
        }
        function readerLoadend(event) {
            var error = reader.error;
            if (!error) {
                startSendContents(reader.result);
            }
            cleanReader();
            if (error) {
                nextFile();
            }
        }
        function startSendContents(contents) {
            xhr = methods.createXMLHttpRequest({
                url: urls['tracdragdrop.new'],
                data: contents,
                headers: {
                    'Content-Type': 'application/octet-stream; filename="' + filename + '"',
                    'X-Requested-With': 'XMLHttpRequest' },
                uploadProgress: uploadProgress, success: uploadSuccess, error: uploadError });
        }
        function readerError(event) {
            setTimeout(function() { showReaderError(file, e) }, 0);
            cleanReader();
            nextFile();
        }
        function readerAbort(event) {
            setTimeout(function() { showReaderError(file, e) }, 0);
            cleanReader();
            nextFile();
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
            var message = xhr.responseText
                        || decodeURIComponent(xhr.getResponseHeader('X-TracDragDrop') || '')
                        || textStatus;
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
            var list = [ methodsHTML5, methodsGears ];
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
    function emptyFunction() { }
});
