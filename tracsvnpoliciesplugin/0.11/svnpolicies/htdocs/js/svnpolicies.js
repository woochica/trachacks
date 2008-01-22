

$(document).ready(function() {
	
	
	// set the UI after the settings in the ini file
	if (! $('input#svnpolicies_enabled').checked()) {
		$('#all_controlls').toggle(400); 
	}
	
	if (! $('input#email_enabled').checked()) {
		$('#email_container').toggle(400); 
	}
	
	if (! $('input#email_attachment').checked()) {
		$('#email_attach_controls').toggle(400); 
	}
	
	if (! $('input#log_message_required').checked()) {
		$('#log_controls').toggle(400); 
	}

	if ( ! $('#advanced_precomit_enabled').checked() ){
		$('#advanced_precomit_content').attr("disabled", "disabled"); 
	}
	
	if ( ! $('#advanced_postcomit_enabled').checked() ){
		$('#advanced_postcomit_content').attr("disabled", "disabled"); 
	}

	if ( ! $('#email_from_enabled').checked() ){
		$('#email_from_address').attr("style", "display: none;"); 
	}
	
	// add the event handlers
	$('input#email_from_enabled').click(function(){
		if ($('#email_from_enabled').checked()) {
			$('#email_from_address').removeAttr("style");
		} else {
			$('#email_from_address').attr("style", "display: none;"); 
		}
	});
	
	
	$('input#svnpolicies_enabled').click(function(){
		$('#all_controlls').toggle(400); 
	});
	
	$('input#email_enabled').click(function(){
		$('#email_container').toggle(400); 
	});
	
	$('input#email_attachment').click(function(){
		$('#email_attach_controls').toggle(400); 
	});
	
	$('input#log_message_required').click(function(){
		$('#log_controls').toggle(400); 
	});

	$('#advanced_postcomit_enabled').click(function(){
		if ( $('#advanced_postcomit_enabled').checked() ) {
			$('#advanced_postcomit_content').removeAttr("disabled"); 
		} else {
			$('#advanced_postcomit_content').attr("disabled", "disabled"); 
		}
	});

	$('#advanced_precomit_enabled').click(function(){
		if ( $('#advanced_precomit_enabled').checked() ) {
			$('#advanced_precomit_content').removeAttr("disabled");
		} else {
			$('#advanced_precomit_content').attr("disabled", "disabled");
		}
	});
	
	
	$('#message_field')
	.animate({opacity: 1.0}, 300)
	.show('slow')
	.animate({opacity: 1.0}, 10000)
	if ($('#backend-message').length == 0) {
		$('#message_field').fadeOut('slow');
	}

	
})
