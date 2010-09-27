$(function() {
  var tips = $(".validate_tips");
  
  function update_tips(t) {
    tips.text(t)
        .addClass("ui-state-highlight");
    setTimeout(function() {
      tips.removeClass("ui-state-highlight");
    }, 1500);
  }
  
  function check_not_empty(o, n) {
    if (o.val().length < 1) {
      o.addClass("ui-state-error");
      update_tips("A " + n + " is required.");
      return false;
    } else {
      return true;
    }
  }

  function check_length(o, n, min, max) {
    if ( o.val().length > max || o.val().length < min ) {
      o.addClass('ui-state-error');
      update_tips("Length of " + n + " must be between " + min + " and " + max + ".");
      return false;
    } else {
      return true;
    }
  }

  function check_regexp(o, regexp, n) {
    if ( !(regexp.test(o.val())) ) {
      o.addClass('ui-state-error');
      update_tips(n);
      return false;
    } else {
      return true;
    }
  }
  
  $("#dialog-bsop_create_folder").dialog({
    autoOpen: false,
    height: 350,
    width: 500,
    modal: true,
    buttons: {
      'Commit': function() {
        var bValid = true;
        $("dialog-bsop_create_folder .bsop_ctl").removeClass('ui-state-error');

        bValid = bValid && check_not_empty($("#bsop_create_folder_name"),
                                           "folder name");
        bValid = bValid && check_not_empty($("#bsop_create_commit"), 
                                           "commit message");
        
        if (bValid) {
          $('#bsop_create_form').trigger('submit');
        }
      },
      Cancel: function() {
        $(this).dialog('close');
      }
    },
    close: function() {
      $("dialog-bsop_create_folder .bsop_ctl").val('')
                                              .removeClass('ui-state-error');
    }
  });

  $("#dialog-bsop_upload").dialog({
    autoOpen: false,
    height: 350,
    width: 500,
    modal: true,
    buttons: {
      'Upload file': function() {
        var bValid = true;
        $("dialog-bsop_upload .bsop_ctl").removeClass('ui-state-error');

        bValid = bValid && check_not_empty($("#bsop_upload_file"), "file");
        bValid = bValid && check_not_empty($("#bsop_upload_commit"), 
                                           "commit message");
        
        if (bValid) {
          $('#bsop_upload_form').trigger('submit');
        }
      },
      Cancel: function() {
        $(this).dialog('close');
      }
    },
    close: function() {
      $("dialog-bsop_upload .bsop_ctl").val('').removeClass('ui-state-error');
    }
  });

  $("#dialog-bsop_move_delete").dialog({
    autoOpen: false,
    height: 350,
    width: 500,
    modal: true,
    buttons: {
      'Commit': function() {
        var bValid = true;
        $("dialog-bsop_move_delete .bsop_ctl").removeClass('ui-state-error');
        
        if ($('#bsop_mvdel_op').val() === "move") {
          bValid = bValid && check_not_empty($("#bsop_mvdel_dst_name"), 
                                             "destination");
        }
        bValid = bValid && check_not_empty($("#bsop_mvdel_commit"), 
                                           "commit message");
        
        if (bValid) {
          $('#bsop_move_delete_form').trigger('submit');
        }
      },
      Cancel: function() {
        $(this).dialog('close');
      }
    },
    close: function() {
      $("dialog-bsop_move_delete .bsop_ctl").val('')
                                            .removeClass('ui-state-error');
    }
  });
  
  // Show dialogs on click of corresponding button
  $('#bsop_upload').click(function() {
    $('#dialog-bsop_upload').dialog('open');
  });
      
  $('#bsop_create_folder').click(function() {
      $('#dialog-bsop_create_folder').dialog('open');
    });
    
  function show_move_delete_dialog(operation, src_items) {
    //var fred = $('#bsop_mvdel_src_name option:selected').length
    
    // Is this a move or a delete? Show/hide the destination field
    if (operation === 'move') {
        $('.bsop_ctl_move').show();
    } else if (operation === 'delete') {
        $('.bsop_ctl_move').hide();
    }
    
    // Populate the move/delete form controls
    $('#bsop_mvdel_op').val(operation);
    $('#bsop_mvdel_src_name').empty();
    $.each(src_items, function(index, value) {
      $('#bsop_mvdel_src_name').append($('<option selected="selected"/>')
                                        .val(value)
                                        .text(value));
    });
                                          
    $('#dialog-bsop_move_delete').dialog('open');
  }
      
  $('.bsop_move, .bsop_delete').live('click', function() {
    // A context menu item has been clicked
    // Ascend the tree to the context-menu, then descend to find the hidden
    // name provided by ContextMenuPlugin, ignore the checkboxes
    var mvdel_src_name = $(this).closest('div.context-menu') 
                                .find('span.filenameholder').text();
      
    if ($(this).hasClass('bsop_move')) {
        show_move_delete_dialog('move', [mvdel_src_name]);
    } else if ($(this).hasClass('bsop_delete')) {
        show_move_delete_dialog('delete', [mvdel_src_name]);
    }
  });
  
  $('#bsop_move, #bsop_delete').bind('click', function() {
    // The Move selected or Delete selected button has been clicked
    // Retrieve which fileselect checkboxes have been checked
    var selected_items = $('td .fileselect:checked');
    var bsop_tips = $('.bsop_tips');
    
    if (selected_items.length === 0) {
      bsop_tips.text('No files or folders selected')
               .addClass("ui-state-highlight");
      setTimeout(function() {
      bsop_tips.removeClass("ui-state-highlight");
      }, 1500);
      return;
    }
    
    // Retrieve the hidden contextmenu name element for each selected item
    // build an array of selected names
    var selected_names = $(selected_items).closest('tr')
                                          .find('span.filenameholder')
                                          .map(function() {
                                               return $(this).text();})
                                          .get();
    
    if ($(this).is('#bsop_move')) {
        show_move_delete_dialog('move', selected_names);
    } else if ($(this).is('#bsop_delete')) {
        show_move_delete_dialog('delete', selected_names);
    }
  });

});
