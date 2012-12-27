jQuery(document).ready(function($) {
	var changes_saved = true;

	window.onbeforeunload = warnNotSaved;

	// TODO: only enable remove_closed if there are closed tickets
	$("#remove_closed").attr('disabled', false);

	$(".backlog_tickets").sortable({
		update : function() {
			list_changed();
		},
		connectWith : '.backlog_tickets'
	}).disableSelection();

	$("#save_order").click(function(){
		updateOrder();
	});

	$("#reset_order").click(function(){
		changes_saved = true;
		$('#ticket_order').attr('value', '');
		$('#tickets_out').attr('value', '');
		return true;
	});

	$("#remove_closed").click(function(){
		if (changes_saved) {
			$('#remove_tickets').attr('value', true);
			return true;
		}
		if (confirm('You have unsaved changes to the ticket order. Do you want to save these changes now?')) {
			$('#remove_tickets').attr('value', 'true');
			return updateOrder();
		} else {
			return false;
		}
	});

	function list_changed() {
		changes_saved = false;
		$('#save_order').attr('disabled', false);
		$('#reset_order').attr('disabled', false);
	}

	function updateOrder() {
		changes_saved = true;
		var order = $('#backlog').sortable('toArray');
		$('#ticket_order').attr('value', order.toString());
		var out = $('#notbacklog').sortable('toArray');
		$('#tickets_out').attr('value', out.toString());
		return true;
	}

	function warnNotSaved() {
		if (changes_saved)
			return null;
		return 'You have changed the backlog, but you have not saved the changes. If you leave before saving your changes will be lost.'
	}
});

