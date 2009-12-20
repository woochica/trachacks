/*
 * javascript:(function(d,u){var s=d.createElement('script');s.charset='utf-8';s.src=u;d.getElementsByTagName('head')[0].appendChild(s)})(document,'http://trac-hacks.org/svn/tracwysiwygplugin/0.11/bookmarklet.js')
 */
(function() {
    var w = window;
    var d = document;
    var base = 'http://trac-hacks.org/svn/tracwysiwygplugin/0.11/tracwysiwyg/htdocs/';
    var head = d.getElementsByTagName('head')[0];
    var script = d.createElement('script');
    script.setAttribute('type', 'text/javascript');
    script.setAttribute('charset', 'utf-8');
    script.src = base + 'wysiwyg.js';
    head.appendChild(script);
    var link = d.createElement('link');
    link.setAttribute('rel', 'stylesheet');
    link.setAttribute('type', 'text/css');
    link.setAttribute('href', base + 'wysiwyg.css');
    head.appendChild(link);

    function getTracPaths() {
        var paths = {};
        var links = head.getElementsByTagName('link');
        var length = links.length;
        for (var i = 0; i < length; i++) {
            var link = links[i];
            var rel = (link.getAttribute('rel') || '').toLowerCase();
            var href = link.getAttribute('href') || '';
            switch (rel) {
            case 'search':
                if (/\/search$/.test(href)) {
                    paths.base = href.slice(0, -6);
                }
                break;
            case 'stylesheet':
                if (/\/css\/trac\.css$/.test(href)) {
                    paths.htdocs = href.slice(0, -12);
                }
                break;
            }
        }
        return paths.base && paths.htdocs ? paths : null;
    }

    function lazy() {
        switch (typeof w.TracWysiwyg) {
        case 'undefined':
            setTimeout(lazy, 100);
            return;
        case 'function':
            TracWysiwyg.getTracPaths = getTracPaths;
            TracWysiwyg.initialize();
            break;
        }
    }
    lazy();
})();
