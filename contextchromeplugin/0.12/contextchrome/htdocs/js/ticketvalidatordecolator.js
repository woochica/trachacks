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
				$('#field-' + field).addClass('tracvalidator');
			}
		}
	}
})(jQuery); 