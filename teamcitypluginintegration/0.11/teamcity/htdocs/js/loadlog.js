$(document).ready(function() {
	$('a.show_log').toggle(
		function(event) {
			event.preventDefault();
			var div = $(this).siblings('.hiddenlog')[0];
			var log_url = $(this).attr('href');
			$(this).text('Hide build log');
			var log = $.ajax({
				url: log_url,
				success: function(data) {
					div.innerHTML = '<pre>'+data+'</pre>';
					$(div).show();
				},
				error: function() {
					div.innerHTML = '<p>Ooops. Loading failed</p>'
					$(div).show();
				}
			})
		},
		function(event) {
			event.preventDefault();
			var div = $(this).siblings('.hiddenlog')[0];
			$(this).text('View build log');
			$(div).hide();
		}
	);
})
