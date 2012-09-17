var changes_saved = true;

$(function() {
	$('.save_order').attr('disabled', true);
	$('.reset_order').attr('disabled', true);
	$(".backlog_tickets").sortable({
		update : function() {
			list_changed();
		},
		connectWith : '.backlog_tickets'
	}).disableSelection();
});

function showOrder() {
	var order = $('#backlog').sortable('toArray');
	var out = $('#notbacklog').sortable('toArray');
	alert(order);
	alert(out);
}

function updateOrder() {
	changes_saved = true;
	var order = $('#backlog').sortable('toArray');
	$('#ticket_order').attr('value', order.toString());
	var out = $('#notbacklog').sortable('toArray');
	$('#tickets_out').attr('value', out.toString());
	return true;
}

function resetOrder() {
	changes_saved = true;
	$('#ticket_order').attr('value', '');
	$('#tickets_out').attr('value', '');
	return true;
}

function warnNotSaved() {
	if (changes_saved)
		return null;
	return 'You have changed the backlog, but you have not saved changes. If you leave before submitting your changes will be lost.'
}

function list_changed() {
	changes_saved = false;
	$('.save_order').attr('disabled', false);
	$('.reset_order').attr('disabled', false);

}

function deleteClosed() {

	if (changes_saved) {
		$('#delete_closed').attr('value', 'true');
		return true;
	}

	if (confirm('You have unsaved changes to the ticket order. Do you want to save these changes now?')) {
		$('#delete_closed').attr('value', 'true');
		return updateOrder();

	} else {
		return false;
	}

}

window.onbeforeunload = warnNotSaved
