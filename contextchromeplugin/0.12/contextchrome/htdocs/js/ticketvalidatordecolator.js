/*
 * Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
	var rules;
	var workflow;
	$(function() {
		// retrieve a configuration
		path = $('#search')[0].action
		path = path.substring(0, path.length - 7)
		$.getJSON(path + "/ticketvalidator.options", function(json) {
			rules = json['rules'];
			workflow = json['workflow'];
			workflow['newticket'] = {newstate: 'new'}
			// bind
			$('#action input[type=radio]').change(addclass);
			// force invoke a select handler
			currentaction = $('#action input[checked=checked]')
			dummyevent = {target:{value:'newticket'}}
			currentaction.length == 0 && addclass(dummyevent) || currentaction.change();
		});
	});

	addclass = function(event) {
		$(".tracvalidator").removeClass('tracvalidator');
		action = event.target.value;
		if (!action in workflow) return;  // error exit
		newstate = workflow[action].newstate
		currentstate = $(".trac-status a").get(0).innerText
		for (field in rules) {
			if (!('status' in rules[field]) 
			|| rules[field].status == newstate 
			|| newstate == '*' && rules[field].status == currentstate) {
				// $('#properties #field-' + field).addClass('tracvalidator');
				// $('label[for=field-' + field + ']').addClass('tracvalidator');
				// $('#properties #field-' + field).parentsUntil("tr","td").prev().addClass('tracvalidator');
				$("#properties [name=field_" + field + "]").addClass('tracvalidator'); // take care for radio buttons
				$("#properties [name=field_" + field + "]").parentsUntil("tr","td").prev().addClass('tracvalidator');
			}
		}
	}
})(jQuery); 