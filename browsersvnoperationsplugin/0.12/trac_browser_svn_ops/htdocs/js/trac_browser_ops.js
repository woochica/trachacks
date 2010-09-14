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
					// TODO Actually send the file 
					$(this).dialog('close');
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
	
	$('#ctxtnav ul li:contains("Upload")').click(function() {
		$('#dialog-bsop_upload').dialog('open');
	});

});
