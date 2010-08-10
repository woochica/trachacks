/*
*   Function attempts to rewrite a table to remove fields that have
*   been removed during stream filtering.
*   Only works for <table>, <thead>, <tbody> and <tfoot> tags.
*   Code by Josh Godsiff, for www.oxideinteractive.com.au
*   Email: josh@oxideinteractive.com.au
*/
$.prototype.cleanupTable = function() {
    if($(this).is('table')) {
        var body = $(this).children('thead, tbody, tfoot');
    } else if($(this).is('thead, tbody, tfoot')) {
        var body = $(this);
    } else {
        return;
    }

    var full = $(body).children('tr').filter(function() {
        return $(this).children('td.fullrow').length > 0;
    });
    $(full).detach();

    var data = $(body).find('tr').children().filter(function() {
        return ($(this).find('span.empty').length == 0 && $(this).is(':not(:empty)'));
    });

    $(body).children('tr').detach();
    $(body).append($(full));

    $(data).each(function(ind, val) {
        if(ind % 4 == 0) {
            $(body).append('<tr class="current"></tr>');
        }

        var col = (ind % 4 <= 1 ? 1 : 2);
        if($(this).children('span.empty').length <= 0) {
            $(this).attr('class', 'col' + col);
            $(body).find('tr.current').append($(this));
        }

        if(ind % 4 == 3) {
            $(body).find('tr.current').removeClass('current');
        }
    });
};

$(document).ready(function() {
   // Give other layout changing functions time to run
   window.setTimeout(function(){
     $('#properties table').cleanupTable();
     $('table.properties').cleanupTable();
   }, 100);
});
