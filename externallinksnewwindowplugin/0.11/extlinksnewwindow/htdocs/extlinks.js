
$(document).ready( function() {
    $('a.ext-link').click ( function () {
        window.open( $(this).attr('href') );
        return false;
    });
});

