var BatchMod = {
	
	// Convenience function for creating a <label>
    createLabel: function(text, htmlFor) {
      var label = $($.htmlFormat("<label>$1</label>", text));
      if (htmlFor)
        label.attr("for", htmlFor).addClass("control");
      return label;
    },
	
	// Convenience function for creating an <input type="text">
    createText: function(name, size) {
      return $($.htmlFormat('<input type="text" name="$1" size="$2">', 
                            name, size));
    },
    
    // Convenience function for creating an <input type="checkbox">
    createCheckbox: function(name, value, id) {
      return $($.htmlFormat('<input type="checkbox" id="$1" name="$2"' +
                            ' value="$3">', id, name, value));
    },
    
    // Convenience function for creating an <input type="radio">
    createRadio: function(name, value, id) {
      // Workaround for IE, otherwise the radio buttons are not selectable
      return $($.htmlFormat('<input type="radio" id="$1" name="$2"' +
                            ' value="$3">', id, name, value));
    },
  
    // Convenience function for creating a <select>
    createSelect: function(name, options, optional) {
        var e = $($.htmlFormat('<select id="$1" name="$1">', name));
        if (optional)
            $("<option>").appendTo(e);
        for (var i = 0; i < options.length; i++) {
            var opt = options[i], v = opt, t = opt;
            if (typeof opt == "object") 
                v = opt.value, t = opt.text;
            $($.htmlFormat('<option value="$1">$2</option>', v, t)).appendTo(e);
        }
        return e;
    },
    
    //Create the appropriate input for the property.
    createInput: function(inputName, property){
        var td = $('<td class="batchmod_property>')
        switch(property.type){
            case 'select':
                td.append(BatchMod.createSelect(inputName, property.options, true));
                break;
            case 'radio':
                for (var i = 0; i < property.options.length; i++) {
                    var option = property.options[i];
                    td.append(BatchMod.createRadio(inputName, option, inputName + "_" + option))
                        .append(" ")
                        .append(BatchMod.createLabel(option ? option : "none", inputName + "_" + option))
                        .append(" ");
                }
                break;
            case 'checkbox':
                td.append(BatchMod.createRadio(inputName, "1", inputName + "_on"))
                    .append(" ").append(BatchMod.createLabel(_("yes"), inputName + "_on"))
                    .append(" ")
                    .append(BatchMod.createRadio(inputName, "0", inputName + "_off"))
                    .append(" ").append(BatchMod.createLabel(_("no"), inputName + "_off"));
                break;
            case 'text':
                td.append(BatchMod.createText(inputName, 42));
                break;
            case 'time':
                td.append(BatchMod.createText(inputName, 42).addClass("time"));
                break;
        }
        return td;
    },
    
    getInputName: function(propertyName){
        return 'bmod_value_' + propertyName;
    },
    
    //Remove the row for the given property. Reenable it in the list.
    removeRow: function(propertyName){
        $('#batchmod_' + propertyName).remove();
        $($.htmlFormat("#add_batchmod_field option[value='$1']", propertyName)).enable();
    }
	
}

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
  
    //Add the new batch modify field when the user selects one from the dropdown.
    $("#add_batchmod_field").change(function() {
        if (this.selectedIndex < 1)
            return;
        
        var propertyName = this.options[this.selectedIndex].value;
        var property = properties[propertyName];
        
        var tr = $("<tr>").attr('id', 'batchmod_' + propertyName);
        
        // Add the remove button
        tr.append($('<td>')
            .append($('<div class="inlinebuttons">')
                .append($('<input type="button" value="&ndash;">')
                    .click(function() { BatchMod.removeRow(propertyName); })
                )
            )
        );
        
        //Add the header row.
        tr.append($('<th scope="row">')
            .append(BatchMod.createLabel(property.label, BatchMod.getInputName(propertyName)))
        );
        
        // Add the input element.
        tr.append(BatchMod.createInput(BatchMod.getInputName(propertyName), property));
        
        //Add the element before the comment box.
        $("#batchmod_comment").before(tr);
                
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