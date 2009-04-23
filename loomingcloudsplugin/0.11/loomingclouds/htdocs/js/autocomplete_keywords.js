$(document).ready(function() {
	$("#field-keywords").autocomplete("tags", {
            extraParams: {format: 'txt'},
	    multiple: true,
            formatItem: formatTags});
});
