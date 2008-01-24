$(document).ready(function() {
    var ticket = /\/ticket\/(\d+)/.exec(document.location)[1];
    $('#changelog h3').each(function() {
        var comment = $('input[@name=replyto]', this)[0];
        if (comment) {
            comment = comment.value;
            $('.inlinebuttons', this).append('<a href="../ticketchangecomment/'+ticket+'?cnum='+comment+'">Change</a>');
        }
    });
});
