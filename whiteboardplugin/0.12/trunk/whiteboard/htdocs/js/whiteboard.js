/*
 * Copyright (C) 2010 Brian Meeker
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

jQuery(document).ready(function($){
    
    //Toggle between the whiteboard and grid being visible.
    function toggleView(visible, hidden){
        //Toggle the whiteboard
        $("#whiteboard_form").toggle();
        
        //Toggle the grid
        $(".report-result").toggle();
        $(".tickets").toggle();
        
        //Toggle the view list styles.
        visible.addClass("not_current");
        hidden.removeClass("not_current");
    }
    
    //Resizes each column to equal heights.
    function resizeColumnTickets(){
        //Find the largest list.
        var largestList = 0;
        $(".column_tickets").each(function(){
            var size = $(this).children("li").size();
            if(size > largestList){
                largestList = size;
            }
        });
        
        //Find the height of each ticket.
        var ticketHeight = $('li.board_ticket').first().height() + 10;
        
        $('.board_column').height(ticketHeight * largestList + 50);
        $('.column_tickets').height(ticketHeight * largestList );
    }
    
    var actions = new Array();
    var customQueryLink = $('#ctxtnav ul li:contains("Custom Query")');
    var whiteboardLink = $('#ctxtnav ul li:contains("Whiteboard")');
    
    $('.board_column').equalHeights()
    $("#whiteboard_form").hide();
    
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
    
    //Keeps track of every action performed.
    $(".column_tickets").bind("sortreceive", function(event, ui){
        actions.push({
            "ticket": /(board_ticket_)(\d)/.exec(ui.item.attr("id"))[2],
            "from": ui.sender.context,
            "to": event.target
        });
    });
    
    //Submit changes made with the whiteboard.
    $("#whiteboard_form").submit(function(){
        try{
            var valid = true;
            var changes = new Array();
            //Get the ticket and the new value for every change.
            for(var i=actions.length-1; i>=0; i--){
                changes.push($.format("$1:$2", actions[i].ticket, actions[i].to.id));
            }
            
            //You must make some changes to be able to save.
            if(changes.length == 0){
                valid = false;
            } else {
                var changesValue = "";
                for(var i=0; i<changes.length; i++){
                    changesValue += changes[i] + ",";
                }
                $("#whiteboard_changes").val(changesValue);
            }
            
            return valid;
        }
        catch(e){
            alert(e);
            return false;
        }
    });
    
});