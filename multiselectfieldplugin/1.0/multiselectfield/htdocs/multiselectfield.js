jQuery(document).ready(function($) {

	jQuery('.multiselect').each(function(i) {
		var select = jQuery(this);
		var value = select.prev().attr('value');
		var options = value.split(' ');

		console.debug("value: '" + value + "'");
		console.debug("options: '" + options + "'");

		var length = options.length;
		for (var optionIndex = 0; optionIndex < length; optionIndex++) {
			if (options[optionIndex] == '') {
				continue;
			}
			select.children("option:contains('" + options[optionIndex] + "')").attr('selected', 'selected');
		}

		select.chosen().change(function(event) {
			var values = jQuery(event.target).val();
			if (values === null)  {
				select.prev().attr('value', '');
			} else {
				select.prev().attr('value', values.join(' '));
			}
			
		});
		
		
		// TODO: register to listen original field event and update the chosen field accordingly
		// (this is needed if user reverts changes when editing. Now the fields just get out of sync.)
	});
});
