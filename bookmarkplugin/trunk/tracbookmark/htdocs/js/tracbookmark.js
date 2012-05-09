$(document).ready(function() {
var bindBookmarkMenu = function() {
    $('#bookmark_menu, #bookmark_menu li').mouseover(function() {
        $(this).find('li').css('display', 'block');
        $(this).find('li:first').css('display', 'inline-block');
    });
    $('#bookmark_menu').mouseout(function() {
        $(this).find('li').hide();
        $(this).find('li:first').show();
    });
}
    $('#bookmark_this').click(function() {
        var button = $(this);

        $.get($(this).attr('href'), function(result) {
            var params = result.split('&');
            button.find('img:first').attr('src', params[0]);
            button.attr('href', params[1]);
            button.attr('title', params[2]);

            var bookmark_path = $('#bookmark_menu li:first a:first').attr('href');
            $.get(bookmark_path, function(result) {
                $('#bookmark_placeholder').html(result);
                bindBookmarkMenu();
            });
        });
        return false;
    });
    bindBookmarkMenu();
});
