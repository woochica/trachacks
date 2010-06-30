jQuery(document).ready(function($){
	
	//Add a new column with checkboxes for each ticket.
	//Selecting a ticket marks it for inclusion in the batch. 
	$("table.listing tr td.id").each(function() {
    	tId=$(this).text().substring(1); 
      	$(this).before('<td><input type="checkbox" name="selectedTicket" class="bmod_selector" value="'+tId+'"/></td>');
    });
  
  	//Add a checkbox at the top of the column to select ever ticket in the group.
  	$("table.listing tr th.id").each(function() { 
		$(this).before('<th class="bmod_selector"><input type="checkbox" name="bmod_toggleGroup" /></th>');
    });

    //Add the click behavior for the group toggle. 
  	$("input[name='bmod_toggleGroup']").click(function() { 
    	$("tr td input.bmod_selector",$(this).parents("table.listing")).attr("checked",this.checked);
  	});
  
  	//By default the comment field is enabled.
  	$("input#bmod_flag_comment").click(function() {enableControl("bmod_value_comment",this.checked);} );
  
  	//At least one ticket must be selected to submit the batch.
  	$("form#batchmod-form").submit(function() {
    	var selectedTix=[];    
    	$("input[name=selectedTicket]:checked").each( function(){ selectedTix.push(this.value);} ); 
    	$("input[name=selectedTickets]").val(selectedTix);
    	if(selectedTix.length == 0){
	        alert("No tickets selected to modify");
    	    return false;
    	}
  	});
  
  	//Collapse the form by default
  	$("#batchmod-fieldset").toggleClass("collapsed");
  
    // Convenience function for creating a <select>
    function createSelect(name, options, optional) {
        var e = $($.htmlFormat('<select name="$1">', name));
        if (optional)
            $("<option>").appendTo(e);
        for (var i = 0; i < options.length; i++) {
            var opt = options[i], v = opt, t = opt;
            if (typeof opt == "object") 
                v = opt.value, t = opt.text;
            $($.htmlFormat('<option value="$1">$2</option>', v, t)).appendTo(e);
        }
        return e;
    }
  
  	//Add the new batch modify field when the user selects one from the dropdown.
  	$("#add_batchmod_field").change(function() {
		if (this.selectedIndex < 1)
        	return;
        
        var propertyName = this.options[this.selectedIndex].value;
        var property = properties[propertyName];
        
        var tr = $("<tr>").addClass('batchmod_' + propertyName);
        // Add the remove button
        tr.append($('<td>')
            .append($('<div class="inlinebuttons">')
                .append($('<input type="button" value="&ndash;">')
                    .click(function() { alert("remove " + propertyName); }))));
        
        $("#batchmod-fieldset table tbody").append(tr);
        
        $("#batchmod-fieldset table tbody")
            .append($('<tr>')
                .append($('<td>')
                    .append($('<label>')
                        .append(propertyName)
                    )
                .append(createSelect(propertyName, property.options, false))
            )
        );
                
		//Add the field to the table. Will need information about the type of input to be inserted for each field.
			//What to do about textareas? They are currently filtered out, but then are handled anyways. Obviously this is never hit.
		//Add a remove button for each field.
		//Insert the new rows in the same order as listed in the dropdown. This is the same behavior as the filters.
		//Rules
			//When Status is set to "closed" a resolution must also be set.
			//Setting a resolution sets the status to closed.
			//Validate these server-side as well.
        
        //Disable each element from the option list when it is selected.
        this.options[this.selectedIndex].disabled = 'disabled'
	});
});