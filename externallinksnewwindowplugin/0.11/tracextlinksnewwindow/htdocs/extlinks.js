/*
    Attaches an onClick event on all links in class ext-link which opens this
    link in a new window.

    Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the GPL v3!
*/

$(document).ready( function() {
    $('a.ext-link').click ( function () {
        window.open( $(this).attr('href') );
        return false;
    });
});

