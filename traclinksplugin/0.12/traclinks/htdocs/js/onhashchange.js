$(document).ready(function() {
	window.onhashchange = function(event) {
		traclinks = $("#proj-search").attr('value');
		if(location.hash.indexOf('#comment:') == 0 && ( i = traclinks.indexOf('ticket:')) >= 0) {
			traclinks = location.hash.slice(1) + ':' + traclinks.slice(i);
			$("#proj-search").attr('value', traclinks);
		} else if(location.hash.indexOf('#L') == 0 && (traclinks.indexOf('source:')) == 0) {
			if(( i = traclinks.indexOf('#')) >= 0)
				traclinks = traclinks.slice(0, i)
			traclinks = traclinks + '#' + location.hash.slice(1)
			$("#proj-search").attr('value', traclinks);
		}
	};
	if(location.hash.length > 0)// invoke it if necessary
		window.onhashchange(null);
});
