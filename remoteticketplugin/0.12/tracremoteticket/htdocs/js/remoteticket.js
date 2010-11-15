$(function() {
    $('#newlinked :submit[name="create"]').bind('click', function() {
        site = $('#remote-site :selected').val();
        href = location.href;
        
        // Direct form submission according to project drop down
        form = $('#newlinked');
        form.attr('action', site);
        
        // If the selected project is this project set the linked_val
        // parameter to the ticket number, otherwise use fully qualified url 
        // of this page
        if (site.charAt(0) === '/' ||
                site.substring(0, site.lastIndexOf('/')) ===
                href.substring(0, href.lastIndexOf('/'))) {
            $('#linked-val').val(href.substring(href.lastIndexOf('/')+1));
        } else {
            $('#linked-val').val(href);
        }
    });
});
