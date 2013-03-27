$(document).ready(function() {
	$('input.project').change(function() {
		$(this).siblings("div").children('input').attr('checked', false);
		$(this).siblings("div").toggle();
	});
});
