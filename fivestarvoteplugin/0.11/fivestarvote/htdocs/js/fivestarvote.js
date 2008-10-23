$(document).ready(function() {
    $('#fivestarvotes').click(function(e) {
        var button = this;
        e.preventDefault();
        $.get(e.target.href + '?js=1', function(result) {
            result = result.split(',');
            $('#fivestarvotes .current-rating').css('width', result[0] + '%').html(result[1]);
            $('#fivestarvotes').attr('title', result[2]);
        });
        return false;
    });
});

