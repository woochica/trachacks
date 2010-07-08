$(document).ready(function() {
        var tagnode = $("#field-keywords");
        $("ul.tagcloud a").click(function() {
                var value = tagnode.val();
                value += ' ' + $(this).text();
                tagnode.val(value);
                return false;
            });
       $(".tag-cloud-filler").click(function(){
       			if($("ul.tagcloud").css("maxHeight")=="40px")
       			{
       			$("ul.tagcloud").css("maxHeight","99999px");
       			$(this).html("Less...");
       			}
       			else
       			{
       			$("ul.tagcloud").css("maxHeight","40px");
       			$(this).html("More...");
       			}
       			return false;
       			});
    });