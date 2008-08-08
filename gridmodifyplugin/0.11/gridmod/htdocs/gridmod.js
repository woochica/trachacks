/* 
 * -*- coding: utf-8 -*-
 * Copyright (C) 2008 Abbywinters.com
 * trac-dev@abbywinters.com
 * Contributor: Zach Miller
 */

if(!window.console)
    window.console = {};
if(!window.console.firebug || !window.console.log)
    window.console.log = function() {};

$(document).ready(function() {
    $(".gridmod_form").each(function(i) {
        var gridmod_default = $.trim($(this).next('.gridmod_default').text());
        $(this).find('option[value="'+gridmod_default+'"]').attr('selected', 'selected');
        $(this).children('select').change(function() {
            var ticket_field = $(this).attr('name');
            var ticket_number = $(this).parents('tr').find('[class="id"],[class="ticket"]').text();
            ticket_number = ticket_number.replace(/[^\d]/g, '');
            var new_value = $(this).find('option:selected').text();

            console.log("Changing "+ticket_field+" for #"+ticket_number+" to "+new_value+".");
            var url = $('link[rel="search"]').attr('href').replace(/\/search/, '');
            url += '/gridmod/update';
            var data = {'ticket': ticket_number};
            data[ticket_field] = new_value;
            $.ajax({
                // Although semantically this should be POST, that doesn't seem to work.
                'type': "GET",
                'url': url,
                'data': data,
                'success': function(){
                    console.log('Updated #'+ticket_number+'.');
                },
                'error': function(){
                    console.log('Failed to update #'+ticket_number+'.');
                }
            });

        });
    });
});
