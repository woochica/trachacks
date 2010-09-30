$(function() {
    function getURLParameter(name) {
        return unescape(
            (RegExp(name + '=' + '(.+?)(&|$)').exec(location.search)||[,null])[1]
        );
    }

    function update_filter(){      
        $('#content > h1 > span').html('<img src="/trac/chrome/aq/image/ajax-loader-small.gif" />');
        
        var dataString = $('#query').serialize();
       
       $.ajax({
            type: "POST",
            url: "/trac/query",
            data: dataString,
            success: function(data) {
                //alert(
                $('.listing').parent().html($("#content > div[id='']:first", data));
                $('#content > h1 > span').html($("#content > h1 > span", data).contents());
            }
        });
    }
    
    
    $(":input[name='update']").bind('click', function() {
        update_filter();
        return false;
    });

    $(":button").bind("click", function(){
        update_filter();
    });
    $("#query").delegate(":input[type!='text'][type!='select-one']", "click", function(){
        update_filter();
    });
    
    $("#query").delegate("input:text",'change', function() {
        update_filter();
    });
    
    $("select").live('focusout', function() {
        update_filter();
    });
});