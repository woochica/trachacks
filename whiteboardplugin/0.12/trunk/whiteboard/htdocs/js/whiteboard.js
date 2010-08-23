// Copyright (C) 2010 Brian Meeker

jQuery(document).ready(function($){
    
    var customQueryLink = $('#ctxtnav ul li:contains("Custom Query")');
    var whiteboardLink = $('#ctxtnav ul li:contains("Whiteboard")');
    
    $('.board_column').equalHeights()
    $("#whiteboard").hide();
    
    whiteboardLink.click(function(){
        //Show the whiteboard
        $("#whiteboard").show();
        
        //Hide the grid.
        $(".report-result").hide();
        $(".tickets").hide();
        
        //Toggle the view list styles.
        customQueryLink.addClass("not_current");
        $(this).removeClass("not_current");
        
        return false;
    });
    
    customQueryLink.click(function(){
        //Hide the whiteboard.
        $("#whiteboard").hide();
        
        //Redisplay the grid.
        $(".report-result").show();
        $(".tickets").show();
        
        //Toggle the view list styles.
        $(this).addClass("not_current");
        whiteboardLink.removeClass("not_current");
        
        return false;
    });
    
    //Sorting
    $(".column_tickets").sortable({
        connectWith: '.column_tickets',
        placeholder: 'ticket_placeholder',
        forcePlaceholderSize: true
    });
    
});