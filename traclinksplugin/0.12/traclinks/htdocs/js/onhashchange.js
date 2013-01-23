$(document).ready(function() {
	jQuery(window).hashchange(function(event) {
		traclinks = $("#proj-search").attr('value');
		if($('#main #ticket').length == 1) { // ticket
			path_elements = document.location.pathname.split('/');
			ticketid = path_elements[path_elements.length - 1];
			if(location.hash.indexOf('#comment:') == 0) { // comment of ticket
				traclinks = location.hash.slice(1) + ':ticket:' + ticketid;
			} else if ($.isNumeric(ticketid)) {
				traclinks = 'ticket:' + ticketid + location.hash;
			} else {
				// pass
			}
			$("#proj-search").attr('value', traclinks);
		}
		if($('#main #wikipage').length == 1) { // wiki
			start = $('link[rel="start"]')[0].href
			hash = document.location.hash
			pagename = document.location.href.slice(start.length+1, -hash.length)
			// take care for WikiStart as start page ... pagename == "" in some case
			traclinks = 'wiki:' + pagename + location.hash
			$("#proj-search").attr('value', traclinks);
		}
		if($('#main #preview').length == 1) { //browser
			// TODO: rewrite this ad-hoc code
			if(( i = traclinks.indexOf('#')) >= 0)
			traclinks = traclinks.slice(0, i)
			traclinks = traclinks + '#' + location.hash.slice(1)
			$("#proj-search").attr('value', traclinks);
		}
	});
	if(location.hash.length > 0) // invoke it if necessary after load
		jQuery(window).hashchange();
});
