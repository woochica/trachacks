jQuery(document).ready(function($) {
    $('#bookmark_this').click(function() {
        var button = $(this);

        $.get($(this).attr('href'), function(result) {
            var params = result.split('&');
            button.find('img:first').attr('src', params[0]);
            button.attr('href', params[1]);
            button.attr('title', params[2]);

            var bookmark_path = button.attr('data-list');
            $.get(bookmark_path, function(result) {
                $('#bookmark_menu').html(result);
            });
        });
        return false;
    });
});
