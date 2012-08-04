jQuery(document).ready(function($) {
    $('#bookmark_this').click(function() {
        var button = $(this);

        $.get($(this).attr('href'), function(result) {
            var params = result.split('&');
            if (params[0] == 'off')
                button.addClass('bookmark_off');
            else
                button.removeClass('bookmark_off');
            button.attr('href', params[1]);
            button.attr('title', params[2]);

            var bookmark_path = button.attr('data-list');
            $.get(bookmark_path, function(result) {
                $('#bookmark_menu').html(result);
            });
        });

        button.blur();
        return false;
    });
});
