jQuery(document).ready(function($) {
	spinnerImageURL = (location.pathname.match("/newticket") ? "" : "../") + "chrome/epochfield/css/spinnerDefault.png";
	$(".datetimeEntry").datetimeEntry({
		datetimeFormat : 'Y-O-D H:M:S',
		spinnerImage : spinnerImageURL
	})
});