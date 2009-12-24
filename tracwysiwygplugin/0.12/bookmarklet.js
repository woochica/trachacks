/*
 * javascript:(function(d,u){var s=d.createElement('script');s.charset='utf-8';s.src=u;d.getElementsByTagName('head')[0].appendChild(s)})(document,'http://trac-hacks.org/svn/tracwysiwygplugin/0.12/bookmarklet.js')
 */
(function() {
    var w = window;
    var d = document;
    var base = 'http://trac-hacks.org/svn/tracwysiwygplugin/0.12/tracwysiwyg/htdocs/';
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
        var paths = { stylesheets: [] };
        var links = head.getElementsByTagName('link');
        var length = links.length;
        for (var i = 0; i < length; i++) {
            var link = links[i];
            var rel = (link.getAttribute('rel') || '').toLowerCase();
            var type = (link.getAttribute('type') || '').toLowerCase();
            var href = link.getAttribute('href') || '';
            switch (rel) {
            case 'help':
                if (!paths.base && /\/wiki\/TracGuide$/.test(href)) {
                    paths.base = href.slice(0, -14);
                }
                break;
            case 'search':
                if (!paths.search && !type && /\/search$/.test(href)) {
                    paths.search = href;
                    paths.base = href.slice(0, -6);
                }
                break;
            case 'stylesheet':
                if (/\/css\/trac\.css$/.test(href)) {
                    paths.stylesheets.push(href);
                }
                break;
            }
        }
        if (paths.base && paths.stylesheets.length > 0) {
            if (!paths.search) {
                paths.search = paths.base + 'search';
            }
            paths.stylesheets.push(base + 'editor.css');
            return paths;
        }
        return null;
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
