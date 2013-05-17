/*
 * Copyright (C) 2013 OpenGroove,Inc.
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

jQuery(document).ready(function($) {
    initializeFilters();
    $("#group").change(function() {
        $("#groupdesc").enable(this.selectedIndex != 0)
    }).change();
    if ($("fieldset legend.foldable").size() > 0)
        $("fieldset legend.foldable").enableFolding(false);
    /* Hide the filters for saved queries. */
    if (window.location.href.search(/[?&]report=[0-9]+/) != -1)
        $("#filters").toggleClass("collapsed");
    /* Hide the columns by default. */
    //$("#sort").toggleClass("collapsed");

    var css = {minWidth: "20px", maxWidth: "80%", padding: "5px",
               borderRadius: "6px", border: "solid 1px #777",
               boxShadow: "4px 4px 4px #555", backgroundColor: "#fff",
               opacity: "1", zIndex: "32767", textAlign: "left"};
    $.balloon.defaults.css = css;
    $.balloon.defaults.classname = 'balloon';

    var current = null;

    var hideBalloon = function() {
        if (current !== null) {
            current.hideBalloon();
            current = null;
        }
    };

    $('body').delegate(':not(.balloon)', 'click', function() {
        if ($(this).parents('.balloon').size() == 0)
            hideBalloon();
    });

    var toggleBalloon = function(target, opts) {
        if (current !== null) {
            current.hideBalloon();
            if (current[0] === target[0]) {
                current = null;
                return;
            }
        }
        if (target.position().top - $(window).scrollTop() < 100)
            opts.position = 'bottom';
        else
            opts.position = 'top';
        if (target.position().left - $(window).scrollLeft() < 100)
            opts.position = 'mid right';
        else if (target.position().left + target.width() - $(window).scrollLeft() > $(window).width() - 100)
            opts.position = 'mid left';
        current = target;
        target.showBalloon(opts);
    };

    $('.ticketcalendar').each(function() {
        var ticketcalendar = $(this);
        var newTicketBox = ticketcalendar.find('.ticketcalendar-newticket-box');
        if (newTicketBox.attr('data-writable')) {
            ticketcalendar.delegate('td', 'click', function() {
                var start_date = $(this).attr('data-for-start-date');
                var due_date = $(this).attr('data-for-due-date');
                newTicketBox.find('span[data=start-date]').text(start_date);
                newTicketBox.find('span[data=due-date]').text(due_date);
                var start = newTicketBox.find('.newticket-start-date');
                start.attr('href', start.attr('data-href') + start_date);
                var due = newTicketBox.find('.newticket-due-date');
                due.attr('href', due.attr('data-href') + due_date);
                toggleBalloon($(this), {contents: newTicketBox.clone().show()});
                return false;
            });
        }
        ticketcalendar.delegate('li:not(.milestone)', 'click', function() {
            hideBalloon();
            $.colorbox({ajax: true, maxWidth: '80%', open: true,
                        href: $(this).attr('data-href'),
                        onCleanup: function() { $('.ticketcalendar-popup-list').hide() }});
            return false;
        });
        ticketcalendar.delegate('li.milestone a', 'click', function() {
            window.open($(this).attr('href'), '_self');
            return false;
        });
        ticketcalendar.delegate('a.open-ticketcalendar-ticket-detail', 'click', function(){
            window.open($(this).attr('href'), '_self');
            return false;
        });
        ticketcalendar.find('.ticketcalendar-macro').each(function() {
            var node = $(this);
            var text = node.find('input');
            node.click(function() {
                if (text.css('display') === 'none') {
                    text.show().focus().css('width', '400px');
                }
                text.select();
            });
            text.blur(function() { text.css('width', '0').hide() });
        });
    });
    $('a.show-all-list').click(function() {
        var href = $(this).attr('href');
        toggleBalloon($(this), {contents: $(href).clone().show()});
        return false;
    });
    $('#ticketcalendar-show-a-month').click(function(){
        $('.ticketcalendar-list .hidden').slideDown();
        $(this).hide();
        return false;
    });
    $('.ticketcalendar-popup-list').hide();
    $('.ticketcalendar-list .hidden').hide();

    $(window).resize(function() {
        var table = $('table.calendar');
        var tdwidth = table.find('td').outerWidth();
        var diff = tdwidth - table.find('li:not(.show)').outerWidth();
        table.find('td > ul > li.milestone.show').each(function(){
            var length = parseInt($(this).attr('data-length'));
            $(this).width(tdwidth * length - diff / 2);
        });
    }).resize();
});
