jQuery(document).ready(function() {
	jQuery('th[title][rel]').each(function() {
		$(this)
		.removeAttr('title')
		.tooltip({ relative: "true",
			effect: "fade", position: "north center",
			tip: $(this).attr('rel')
			});
	});
});


