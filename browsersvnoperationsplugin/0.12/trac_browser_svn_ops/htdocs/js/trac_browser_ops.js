$(function() {
	
	var up_file = $("#bsop_upload_file"),
		up_commit = $("#bsop_upload_commit"),
		allFields = $([]).add(up_file).add(up_commit),
		tips = $(".validateTips");
	
	$("#dialog-bsop_create_folder").dialog({
		autoOpen: false,
		height: 350,
		width: 500,
		modal: true,
		buttons: {
			'Commit': function() {
				var bValid = true;
				allFields.removeClass('ui-state-error');

				/* TODO Validation */
				
				if (bValid) {
					$('#bsop_create_form').trigger('submit');
				}
			},
			Cancel: function() {
				$(this).dialog('close');
			}
		},
		close: function() {
			allFields.val('').removeClass('ui-state-error');
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
				allFields.removeClass('ui-state-error');

				/* TODO Validation */
				
				if (bValid) {
					$('#bsop_upload_form').trigger('submit');
				}
			},
			Cancel: function() {
				$(this).dialog('close');
			}
		},
		close: function() {
			allFields.val('').removeClass('ui-state-error');
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
				allFields.removeClass('ui-state-error');

				/* TODO Validation */
				
				if (bValid) {
					$('#bsop_move_delete_form').trigger('submit');
				}
			},
			Cancel: function() {
				$(this).dialog('close');
			}
		},
		close: function() {
			allFields.val('').removeClass('ui-state-error');
		}
	});
	
	// Show dialogs on click of corresponding button
	$('#bsop_upload').click(function() {
		$('#dialog-bsop_upload').dialog('open');
	});
    	
	$('#bsop_create_folder').click(function() {
	    $('#dialog-bsop_create_folder').dialog('open');
    });
    
	$('.bsop_move, .bsop_delete').click(function() {
	    var mvdel_op = '';
	    var mvdel_src_name = $(this).closest('td.name') 
                                    .find('a.dir, a.file').text();
        
        // Is this a move or a delete? Show the destination field
        if ($(this).hasClass('bsop_move')) {
            mvdel_op = 'move';
            $('#bsop_mvdel_dst_name').show();
        } else if ($(this).hasClass('bsop_delete')) {
            mvdel_op = 'delete';
            $('#bsop_mvdel_dst_name').hide();
        }
        
        $('#bsop_mvdel_op').val(mvdel_op);
        $('#bsop_mvdel_src_name').val(mvdel_src_name);
        
        $('#dialog-bsop_move_delete').dialog('open');
	});

});
