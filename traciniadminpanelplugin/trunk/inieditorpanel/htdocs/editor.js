var settings_stored_values = new Object();
var settings_input_fields = new Object();

function update_section_info(section_name, count_diff, modified_diff, defaults_diff) {
  var section_counter = section_counters[section_name];    
  var info_elem = section_counter['info_elem'];
  
  section_counter['option_count'] += count_diff;
  section_counter['defaults_count'] += defaults_diff;
  section_counter['modified_count'] += modified_diff;
  
  info_elem.html( text_modified + section_counter['modified_count'] 
                 + text_defaults + section_counter['defaults_count'] 
                 + text_optionscount + section_counter['option_count']);
}

// Returns jquery result for the specified field
function get_option_input_field(field_name) {
  var input_fields = settings_input_fields[field_name];
  if (input_fields != null) {
    return input_fields;
  }
  
  input_fields = settings_list.find('input[name=\'inieditor_value##' + field_name + '\']');
  if (input_fields.length == 0) {
    // Not an input field but select field
    input_fields = settings_list.find('select[name=\'inieditor_value##' + field_name + '\']');
  }
  
  settings_input_fields[field_name] = input_fields;
  return input_fields;
}

function get_option_cur_value(input_field) {
  if (typeof input_field == 'string') {
    input_field = get_option_input_field(input_field);
  }
  
  if (input_field.length == 1) {
    input_field = input_field;
    switch (input_field[0].nodeName.toLowerCase()) {
      case 'select':
        return input_field.children('option:selected').val();
        
      default:
        return input_field.val();
    }
  } else if (input_field.length > 1 && input_field[0].nodeName.toLowerCase() == 'input') {
    return input_field.filter(':checked').val(); // Note that checkboxes will return an array (?)
  }
}

function check_for_changes() {
  if (section_count == 1) {
    return (section_counters[section_names[0]]['modified_count'] != 0);
  } else if (section_count > 1) {
    for (var i = 0; i < section_count; i++) {
      if (section_counters[section_names[i]]['modified_count'] != 0) {
        return true;
      }
    }
  }
  
  return false;
}

$(document).ready(function(){
  settings_list = $('#settings_table'); // global var
  section_counters = new Object();
  section_names = new Array();
  cur_focused_field = settings_list.find('input[name="inieditor_cur_focused_field"]');
  
  load_data(section_counters, settings_stored_values);

  settings_list.find('input:checkbox[name=inieditor_default]').each(function() {
    var field_name = $(this).val();
    var name_split  = field_name.split('##');
    var section_name = name_split[0].replace(/:/g,'_');
    var option_name = name_split[1];
    var input_field = get_option_input_field(field_name);
    
    // Count section options, setup fields (default, modified), and add register 
    // listener to checkboxes that enables or disables the related input field.    
    var section_counter = section_counters[section_name];    
    
    // Default values
    if ($(this).is(':checked')) {
      section_counter['defaults_count']++;
      input_field.attr('disabled', true);
    }

    // only add triggers if the option is modifiable
    if (!$(this).attr('disabled')) {
      var stored_value = settings_stored_values[section_name][option_name];
      var containing_row = $(this).parents('tr');
      
      if (stored_value == null) {
        stored_value = ''; // mainly for passwords
      }
    
      // Register listeners
      $(this).change(function() {
        if ($(this).is(':checked')) {
          input_field.attr('disabled', true);
          update_section_info(section_name, 0, 0, 1);
        } else {
          input_field.removeAttr('disabled');
          update_section_info(section_name, 0, 0, -1);
        }
      });
      
      // Modified values
      if (get_option_cur_value(input_field) != stored_value) {
        section_counter['modified_count']++;
        containing_row.addClass('modified-field');
      }
      
      // Add triggers for detecting changed values 
      input_field.keyup(function() {
        var wasModified = containing_row.hasClass('modified-field');
        if (get_option_cur_value(input_field) == stored_value) {
          containing_row.removeClass('modified-field');
          if (wasModified) {
            // Only if it actually was modified
            update_section_info(section_name, 0, -1, 0);
          }
        } else {
          containing_row.addClass('modified-field');
          if (!wasModified) {
            // Only if it actually was not modified
            update_section_info(section_name, 0, 1, 0);
          }
        }
      });
      input_field.change(function() {
        var wasModified = containing_row.hasClass('modified-field');
        if (get_option_cur_value(input_field) == stored_value) {
          containing_row.removeClass('modified-field');
          if (wasModified) {
            // Only if it actually was modified
            update_section_info(section_name, 0, -1, 0);
          }
        } else {
          containing_row.addClass('modified-field');
          if (!wasModified) {
            // Only if it actually was not modified
            update_section_info(section_name, 0, 1, 0);
          }
        }
      });
      
      // Add trigger to notify about the currently focused field type; used to
      // determine the pressed submit button when hitting return
      input_field.focus(function() {
        cur_focused_field.val('option-value-' + section_name);
      });
    }    
  });
  
  // Add trigger to notify about the currently focused field type; used to
  // determine the pressed submit button when hitting return
  settings_list.find('input[name^="new-options-"]').focus(function() {
    cur_focused_field.val($(this).attr('name'));
  });
  
  // Same trigger. NOTE: We can't use "click" here as this is also triggered
  // when hitting return. We need to use "focus" here.
  settings_list.find(':submit').focus(function() {
    cur_focused_field.val('');
  });
  
  // Register click listener for expanding/collpasing sections.
  // Update section information.
  settings_list.find('td.section-title').each(function() {
    var section_name = $(this).attr('id').substr('section-title'.length + 1);
    section_names.push(section_name);
    update_section_info(section_name, 0, 0, 0);
    
    if (section_count > 1) { // only make hidable when showing all sections
      var rows = settings_list.find('tr.collapsible-' + section_name);
      
      $(this).click(function() {
        if ($(this).hasClass('header-collapsed')) {
          rows.show();
          $(this).removeClass('header-collapsed');
          $(this).addClass('header-expanded');
        } else {
          rows.hide();
          $(this).removeClass('header-expanded');
          $(this).addClass('header-collapsed');
        }
      });
      
      $(this).addClass('header-collapsed');
      rows.hide();
    }
  });
  
  // Change section form handling
  $('#change-section-name').change(function() {
    $(this).parents('form').submit();
  });
  
  var cur_section = $('#change-section-name option:selected').val();
  $('#select_section_form form').submit(function() {
    var new_section = $('#change-section-name option:selected').val();
    if (cur_section == new_section || new_section == '') {
      return false;
    }
    
    if (check_for_changes() && !confirm('You have unsaved changes in this section. Do you still want to change the section?')) {
      $(this)[0].reset(); // restore current section
      return false;
    }
    
    $(this).find(':submit').attr('disabled', true); 
    return true;
  });

  // New section form handling
  $('#new_section_form form').submit(function() {
    if (check_for_changes() && !confirm('You have unsaved changes in this section. Do you still want to change the section?')) {
      return false;
    }
    
    return true;
  });
});
