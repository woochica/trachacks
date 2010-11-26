$(document).ready(function () {
    $('#newlinked :submit[name="create"]').bind('click', function () {
        var site = $('#remote-site :selected').val();
        
        // Direct form submission according to project drop down
        var form = $('#newlinked');
        form.attr('action', site);
        
        // If the selected project is this project set the linked_val
        // parameter to the ticket number, otherwise use fully qualified url 
        // of this page
        if (site.charAt(0) === '/' ||
                site.substring(0, site.lastIndexOf('/')) ===
                location.href.substring(0, location.href.lastIndexOf('/'))
                ) {
            var tkt_id = location.pathname.substring(
                            location.pathname.lastIndexOf('/') + 1);
            $('#linked-val').val(tkt_id);
        } else {
            $('#linked-val').val(location.href);
        }
    });
});
