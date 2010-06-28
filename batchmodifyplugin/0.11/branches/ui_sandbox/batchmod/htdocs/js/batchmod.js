(function($){
	
	$("#batchmod-fieldset select[name^=add_batchmod_field]").change(function() {
		alert("test")
    }).next("div.inlinebuttons").remove();

})(jQuery);