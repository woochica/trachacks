$(function() {
	
	var name = $("#name"),
		email = $("#email"),
		password = $("#password"),
		allFields = $([]).add(name).add(email).add(password),
		tips = $(".validateTips");
	
	$("#dialog-bsop_open").dialog({
		autoOpen: false,
		height: 500,
		width: 350,
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
	
	
	
	$('#show_upload')
		.button()
		.click(function() {
			$('#dialog-form').dialog('open');
		});

});
