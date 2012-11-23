jQuery(document).ready(function() {
	jQuery('th[title][rel], label[title][rel]').each(function() {
		$(this).removeAttr('title');
		$(this).powerTip({
			placement: 'n',
			mouseOnToPopup: "true"
			});
		$(this).data('powertiptarget', $(this).attr('rel').substring(1));
	});
});