function ToggleShow(obj) {
	$(obj).toggle();
}

$(function(){
	$("area")
	.each(function(){
		$(this).attr("href-bak", $(this).attr("href"));
	})
	.click(function(e){
		$("#nar-detail")
		.load($(this).attr("href-bak"))
		.css({"top": e.pageY, "left": e.pageX})
		.show();
		return false;
	});
});

