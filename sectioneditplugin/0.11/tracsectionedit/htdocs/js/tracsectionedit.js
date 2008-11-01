(function($){
	$.fn.addEditlink = function(title){
		var cnt = 1;
		title = title || "Edit this section";
		return this.filter("*[@id]").each(function(){
			$("<a class='anchor'>[<span>edit</span>]</a>").attr("href", "?action=edit&section=" + cnt++).attr("title", title).appendTo(this);
		});
	}
	
	$(document).ready(function() {
		 $(":header", $("#content")).addEditlink("Edit this section");
    });
})(jQuery);