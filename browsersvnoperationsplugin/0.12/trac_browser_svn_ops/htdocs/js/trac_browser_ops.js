$(function() {
	
	var up_file = $("#bsop_upload_file"),
		up_commit = $("#bsop_upload_commit"),
		allFields = $([]).add(up_file).add(up_commit),
		tips = $(".validateTips");
	
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
			'Upload file': function() {
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
	
	// Show upload dialog on click of  Upload in the context nagivgation area
	$('#ctxtnav ul li:contains("Upload")').click(function() {
		$('#dialog-bsop_upload').dialog('open');
	});
	
	$('.bsop_move, .bsop_delete').click(function() {
	    var mvdel_op = '';
	    var mvdel_name = $(this).closest('td.name') 
                                .find('a.dir, a.file').text();
        var mvdel_base = $('#bsop_mvdel_base').val();
        var mvdel_path = mvdel_base.replace(/\/$/, '')
                                   .concat('/', mvdel_name);
        
        if ($(this).hasClass('bsop_move')) {
            mvdel_op = 'move';
        } else if ($(this).hasClass('bsop_delete')) {
            mvdel_op = 'delete';
        }
        
        $('#bsop_mvdel_op').val(mvdel_op);
        $('#bsop_mvdel_base').val(mvdel_base);
        $('#bsop_mvdel_path').val(mvdel_path);
        
        $('#dialog-bsop_move_delete').dialog('open');
	});

});
