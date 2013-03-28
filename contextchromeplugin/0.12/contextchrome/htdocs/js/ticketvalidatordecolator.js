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
            $('select#field-type').change(addclass);
			// force invoke a select handler on document.ready
			currentaction = $('#action input[checked=checked]')
			dummyevent = {target:{'id':'action_', value:'newticket'}}
			currentaction.length == 0 && addclass(dummyevent) || currentaction.change();
		});
	});

	addclass = function(event) {
		$(".tracvalidator").removeClass('tracvalidator');  // purge
		// Generate condition
		var type = $('#field-type option:selected').text();
		var node = false;
		var action = event.target.id.substring(0,7) == 'action_' && event.target.value ||
		             (node = $('#action input[checked=checked]')[0]) && node.value || 'newticket';
		if (!action in workflow) return;  // error exit
		var state = workflow[action].newstate
		// TODO: a line below will be fixed; after preview or auto_preview, .trac-status reflects invalid current status
		if (state == '*') state = $(".trac-status a").get(0).innerText  // if wildcard, use a current state
		rule = {}
        jQuery.extend(rule, rules['status=' + state + '&type=' + type])
        jQuery.extend(rule, rules['status=*&type=' + type])
        jQuery.extend(rule, rules['status=' + state + '&type=*'])
        jQuery.extend(rule, rules['status=*&type=*'])
		// UI Change
		for (field in rule) {
			$("#properties [name=field_" + field + "]").addClass('tracvalidator'); // take care for radio buttons
			$("#properties [name=field_" + field + "]").parentsUntil("tr","td").prev().addClass('tracvalidator');
		}
	}
})(jQuery); 