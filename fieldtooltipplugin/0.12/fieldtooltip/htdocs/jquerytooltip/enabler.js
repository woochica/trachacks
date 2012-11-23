jQuery(document).ready(function() {
	jQuery('th[title][rel]').each(function() {
		$(this).tooltip( 
		{
			bodyHandler : function() {
				return $($(this).attr('rel'))[0].textContent;
			},
			showURL : false
		});
	});
});

