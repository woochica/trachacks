$(function() {
    $('#newlinked :submit[name="create"]').bind('click', function() {
        form = $('#newlinked');
        site = $('#remote-site :selected').val();
        form.attr('action', site);
    });
});
