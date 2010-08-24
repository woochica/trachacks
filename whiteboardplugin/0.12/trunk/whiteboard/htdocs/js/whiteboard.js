// Copyright (C) 2010 Brian Meeker

jQuery(document).ready(function($){
    
    //Toggle between the whiteboard and grid being visible.
    function toggleView(visible, hidden){
        //Toggle the whiteboard
        $("#whiteboard").toggle();
        
        //Toggle the grid
        $(".report-result").toggle();
        $(".tickets").toggle();
        
        //Toggle the view list styles.
        visible.addClass("not_current");
        hidden.removeClass("not_current");
    }
    
    //Resizes each column to equal heights.
    function resizeColumnTickets(){
        var maxHeight = 0;
        $(".column_tickets").each(function(){
            if($(this).height() > maxHeight){
                maxHeight = $(this).height();
            }
        });
        
        $('.board_column').equalHeights(maxHeight + 60)
    }
    
    var customQueryLink = $('#ctxtnav ul li:contains("Custom Query")');
    var whiteboardLink = $('#ctxtnav ul li:contains("Whiteboard")');
    
    $('.board_column').equalHeights()
    $("#whiteboard").hide();
    
    whiteboardLink.click(function(){
        toggleView(customQueryLink, whiteboardLink)
        return false;
    });
    
    customQueryLink.click(function(){
        toggleView(whiteboardLink, customQueryLink)
        return false;
    });
    
    //Sorting
    $(".column_tickets").sortable({
        connectWith: '.column_tickets',
        placeholder: 'ticket_placeholder',
        forcePlaceholderSize: true
    });
    
    $(".column_tickets").bind("sortover", function(event, ui){
        resizeColumnTickets();
    });
    
});