$(document).ready(function() {
    $("div.mindmap").each(function() {
        var div = $(this);
        var obj = div.children("object");
        obj = obj[0];
        if ($(obj).attr("type") != "application/x-shockwave-flash") {
            return;
        }
        params = {
            version: "6.0",
            width: $(obj).attr("width"),
            height: $(obj).attr("height"),
            onFail: function() {
                div.wrapInner("<div style='display:table-cell;vertical-align:middle'></div>");
                div.css({
                    width: params['width'],
                    height: params['height'],
                    'text-align': 'center',
                    'display': 'table',
                    border: 'solid thin'
                });
                return;
            },
            src: $(obj).attr("data")
        };

        $(obj).children("param").each(function() {
            params[$(this).attr("name")] = $(this).attr("value");
        });
        v = params["version"].split(".");
        if (v[2]) {
            v[1] = v[2];
        }
        params["version"] = [parseInt(v[0]), parseInt("0" + v[1])];
        //div.empty();
        div.flashembed(params);

        //if (jQuery.resizable) {
        //}
    });
    $("div.mindmap").each(function() {
        var div = $(this);
        var obj = div.children("object");
        obj = obj[0];
        $(this).resizable({alsoResize:obj});
    });
});

