$(document).ready(function() {
        var tagnode = $("#field-keywords");
        $("ul.tagcloud a").click(function() {
                var value = tagnode.val();
                value += ' ' + $(this).text();
                tagnode.val(value);
                return false;
            });
    });