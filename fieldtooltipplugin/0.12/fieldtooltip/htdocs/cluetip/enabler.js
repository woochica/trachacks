jQuery(document).ready(function() {
	jQuery('th[title][rel]').each(function() {
		$(this).removeAttr('title');
		$(this).cluetip({  
//			splitTitle: '|',  
			local: true  
		});
	});
});