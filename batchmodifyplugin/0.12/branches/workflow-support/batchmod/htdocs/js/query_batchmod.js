// Copyright (C) 2010 Brian Meeker

jQuery(document).ready(function($){

    //At least one ticket must be selected.
    function validateTicketSelected(){
        var selectedTix=[];    
        $("input[name=selectedTicket]:checked").each( function(){ selectedTix.push(this.value);} ); 
        $("input[name=selectedTickets]").val(selectedTix);
        
        //At least one ticket must be selected.
        if(selectedTix.length === 0){
            $("#batchmod_submit").after('<span class="batchmod_required">You must select at least one ticket.</span>');
            return false;
        } else {
            return true;
        }
    }

    //Add a new column with checkboxes for each ticket.
    //Selecting a ticket marks it for inclusion in the batch. 
    $("table.listing tr td.id").each(function() {
        tId=$(this).text().substring(1); 
        $(this).before('<td><input type="checkbox" name="selectedTicket" class="batchmod_selector" value="'+tId+'"/></td>');
    });

    //Add a checkbox at the top of the column to select ever ticket in the group.
    $("table.listing tr th.id").each(function() { 
        $(this).before('<th class="batchmod_selector"><input type="checkbox" name="batchmod_toggleGroup" /></th>');
    });

    //Add the click behavior for the group toggle. 
    $("input[name='batchmod_toggleGroup']").click(function() { 
        $("tr td input.batchmod_selector",$(this).parents("table.listing")).attr("checked",this.checked);
    });
    
    //Perform validation before submitting the form.
    $("form#batchmod_form").submit(function() {
        //First remove all existing validation messages.
        $(".batchmod_required").remove();
        
        return validateTicketSelected();
    });
});
