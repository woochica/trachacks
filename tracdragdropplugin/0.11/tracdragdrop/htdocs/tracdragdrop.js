jQuery(document).ready(function($) {
    try {
        new FileReader();
        var xhr = new XMLHttpRequest();
        if (!xhr.upload) {
            return;
        }
    }
    catch (e) {
        return;
    }
    var url = getUploadUrl();
    if (!url) {
        return;
    }
    var indicator =
        $('<div id="tracdragdrop_indicator">Enable drap-and-drop attachments</div>')
        .appendTo(document.body);
    var queueFiles = [];
    var countFiles = 0;
    var target = $(document.body);
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

    function dragenter(event) {
        var transfer = event.originalEvent.dataTransfer;
        var types = transfer.types;
        var length = types.length;
        for (var i = 0; i < length; i++) {
            if (types[i] == 'Files') {
                indicator.addClass('active');
                return false;
            }
        }
    }
    function dragleave(event) {
        indicator.removeClass('active');
        return false;
    }
    function dragover(event) {
        return false;
    }
    function drop(event) {
        var transfer = event.originalEvent.dataTransfer;
        var files = transfer.files;
        var length = files.length;
        if (length == 0) {
            return;
        }
        if (!confirm('Are you sure you want to attach files?')) {
            return;
        }
        for (var i = 0; i < length; i++) {
            queueFiles.push(files[i]);
        }
        countFiles += length;
        event.stopPropagation();
        if (notice === null) {
            startUpload();
        }
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
            reader = new FileReader();
            reader.addEventListener('loadend', readerLoadend, false);
            reader.readAsBinaryString(file);
        }
        function nextFile() {
            xhr.upload.removeEventListener('progress', uploadProgress, false);
            xhr.upload.removeEventListener('load', uploadLoad, false);
            xhr.upload.removeEventListener('error', uploadError, false);
            xhr.upload.removeEventListener('abort', uploadAbort, false);
            xhr = null;
            if (queueFiles.length === 0) {
                endUpload();
            }
            else {
                startReader();
            }
        }
        function readerLoadend(event) {
            if (!reader.error) {
                xhr = new XMLHttpRequest();
                xhr.upload.addEventListener('progress', uploadProgress, false);
                xhr.upload.addEventListener('load', uploadLoad, false);
                xhr.upload.addEventListener('error', uploadError, false);
                xhr.upload.addEventListener('abort', uploadAbort, false);
                xhr.open('POST', url, true);
                xhr.setRequestHeader('Content-Type', 'application/octet-stream; filename="' + filename + '"');
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.sendAsBinary(reader.result);
            }
            reader.removeEventListener('loadend', readerLoadend, false);
            reader = null;
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
        function uploadLoad(event) {
            showProgress(100);
            nextFile();
        }
        function uploadError(event) {
            nextFile();
        }
        function uploadAbort(event) {
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
    }
    function getUploadUrl() {
        var head = document.getElementsByTagName('head')[0];
        var links = head.getElementsByTagName('link');
        var length = links.length;
        for (var i = 0; i < length; i++) {
            var link = links[i];
            var rel = link.getAttribute('rel');
            var href = link.getAttribute('href');
            if (rel === 'tracdragdrop.upload' && href !== null) {
                return href;
            }
        }
        return null;
    }
});
