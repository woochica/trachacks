// Copyright (C) 2010 Brian Meeker

jQuery(document).ready(function($){
    
    var viewToggle = $('<div id="view_toggle" class="nav">').append($('<ul>')
        .append('<li id="view_grid" class="first">Grid</li><li id="view_whiteboard" class="not_current last">Whiteboard</li>')
    );
    $('#query').after(viewToggle);
    
    $("#view_whiteboard").click(function(){
        //Pull out all the ticket information, if needed.
        
        //Hide the grid.
        $(".report-result").hide();
        $(".tickets").hide();
        
        //Build the whiteboard and insert it.
        var whiteboard = $('<div id="whiteboard">');
        $('#query').after(whiteboard);
        
        //Toggle the view list styles.
        $("#view_grid").addClass("not_current");
        $("#view_whiteboard").removeClass("not_current");
    });
    
    $("#view_grid").click(function(){
        //Hide the whiteboard.
        $("#whiteboard").slideUp('slow', function(){
            $(this).hide();
        });
        
        //Redisplay the grid.
        $(".report-result").show();
        $(".tickets").show();
        
        //Toggle the view list styles.
        $("#view_whiteboard").addClass("not_current");
        $("#view_grid").removeClass("not_current");
    });
    
});