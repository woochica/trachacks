$(function() {
  var tips = $(".validate_tips");
  
  function update_tips(t) {
    tips.text(t)
        .addClass("ui-state-highlight");
    setTimeout(function() {
      tips.removeClass("ui-state-highlight");
    }, 500);
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
    
  $('.bsop_move, .bsop_delete').live('click', function() {
      var mvdel_op = '';
      
      // Ascend the tree to the context-menu, then descend to find the hidden
      // node name provided by ContextMenuPlugin
      var mvdel_src_name = $(this).closest('div.context-menu') 
                                  .find('span.filenameholder').text();
        
        // Is this a move or a delete? Show the destination field
        if ($(this).hasClass('bsop_move')) {
            mvdel_op = 'move';
            $('#bsop_mvdel_dst_name').show();
        } else if ($(this).hasClass('bsop_delete')) {
            mvdel_op = 'delete';
            $('#bsop_mvdel_dst_name').hide();
        }
        
        $('#bsop_mvdel_op').val(mvdel_op);
        $('#bsop_mvdel_src_name').empty();
        $('#bsop_mvdel_src_name').append($('<option selected="selected"/>')
                                            .val(mvdel_src_name)
                                            .text(mvdel_src_name));
        
        $('#dialog-bsop_move_delete').dialog('open');
  });

});
