jQuery(document).ready(function($) {
    var data = window.tractimedeltaupdator;
    if (!data) {
        return;
    }

    function parse_iso8601(text) {
        var m = /^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)(Z|[-+](\d+):(\d+))$/
                .exec(text);
        if (m !== null) {
            var t = Date.UTC(m[1], +m[2] - 1, m[3], m[4], m[5], m[6]);
            if (m[7] !== 'Z') {
                var tzoffset = (+m[8] * 60 + +m[9]) * 60 * 1000;
                t += m[7].charAt(0) === '+' ? -tzoffset : +tzoffset;
            }
            return t;
        }
        return null;
    }

    var base_url = $('link[rel=help]').attr('href');
    if (!base_url) {
        return;
    }
    base_url = base_url.replace(/\/wiki\/TracGuide$/, '/');
    var adjust = parse_iso8601(data.starttime);
    if (adjust === null) {
        return;
    }
    var starttime = (new Date).valueOf();
    adjust -= starttime;
    var pluralexpr = new Function('n', 'return +(' + data.pluralexpr + ')');
    var units = data.units;

    $('a.timeline, [data-tractimedeltaupdator-time]').each(function() {
        var node = $(this);
        var time = node.attr('data-tractimedeltaupdator-time');
        if (!time) {
            var href = node.attr('href');
            var pos = href.indexOf('?');
            if (pos === -1) {
                return;
            }
            var pairs = href.substring(pos + 1).split(/&/);
            var length = pairs.length;
            for (var i = 0; i < length; i++) {
                var pair = pairs[i];
                if (pair.substring(0, 5) !== 'from=') {
                    continue;
                }
                time = decodeURIComponent(pair.substring(5));
                break;
            }
        }
        if (time) {
            time = parse_iso8601(time);
            if (time !== null) {
                node.attr('data-tractimedeltaupdator', time);
            }
        }
    });

    function pretty_timedelta(t1, t2) {
        var age = Math.abs((t1 - t2) / 1000);
        var length = units.length;
        var unit;
        var num;
        for (var i = 0; i < length; i++) {
            unit = units[i];
            num = age / unit[0];
            if (num >= 1.9) {
                break;
            }
        }
        var format = unit[1];
        num = Math.round(num);
        return babel.format(format[pluralexpr(num)], {num: num});
    }

    function timeline_anchor(node, title) {
        var attrs = {};
        $.each(['data-tractimedeltaupdator',
                'data-tractimedeltaupdator-format',
                'data-tractimedeltaupdator-time',
                'data-tractimedeltaupdator-dateonly'],
                function(idx, name) { attrs[name] = node.attr(name) });
        attrs.title = title || node.attr('title');
        attrs.href = base_url + 'timeline?'
                   + $.param({from: attrs['data-tractimedeltaupdator-time'],
                              precision: 'second'});
        return $('<a class="timeline" />').attr(attrs).text(node.text());
    }

    function updator() {
        var now = (new Date).valueOf() + adjust;
        var delta = 86400000;
        $('[data-tractimedeltaupdator]').each(function() {
            var node = $(this);
            var t = node.attr('data-tractimedeltaupdator');
            if (!t) {
                return;
            }
            delta = Math.min(Math.abs(now - t), delta);
            var relative = pretty_timedelta(t, now);
            var dateinfo = node.attr('data-tractimedeltaupdator-format') ||
                           data.format;
            switch (dateinfo) {
            case 'relative': // 1.0+
                var format = data.relative[now < t ? 'future' : 'past'];
                if (!node.attr('data-tractimedeltaupdator-dateonly')) {
                    relative = babel.format(format, {relative: relative});
                }
                if (t < now && !this.href) {
                    node.replaceWith(timeline_anchor(node));
                }
                else {
                    node.text(relative);
                }
                break;
            case 'absolute': // 1.0+
            case 'date': case 'datetime': // 1.1+
                var format = data.absolute[now < t ? 'future' : 'past'];
                relative = babel.format(format, {relative: relative});
                if (t < now && !this.href) {
                    node.replaceWith(timeline_anchor(node, relative));
                }
                else {
                    node.attr('title', relative);
                }
                break;
            default: // 0.12.x
                node.text(relative);
                break;
            }
        });

        delta /= 1000;
        var interval = delta < 60 * 1.9 ? 10 : delta < 3600 * 1.9 ? 60 : 3600;
        setTimeout(updator, interval * 1000);
    }
    setTimeout(updator, 5000);
});
