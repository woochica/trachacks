$(document).ready(function() {
    function update_filter(){      
        $('#content > h1 > span').html('<img src="/trac/chrome/aq/image/ajax-loader-small.gif" />');
        //$('#example-placeholder').html('<p><img src="/images/ajax-loader.gif" width="220" height="19" /></p>');
        
        var dataString = $('#query').serialize();
        
        $.ajax({
            type: "POST",
            url: "/trac/query",
            data: dataString,
            success: function(data) {
                //alert(
                $('.listing').parent().html($("#content > div[id='']:first", data));
                $('#content > h1 > span').html($("#content > h1 > span", data).contents());
                //$('.listing').html($(data).filter('table.listing'));
                // $('#message').html("<h2>Contact Form Submitted!</h2>")
                    // .append("<p>We will be in touch soon.</p>")
                    // .hide()
                    // .fadeIn(1500, function() {
                        // $('#message').append("<img id='checkmark' src='images/check.png' />");
                    // });
            }
        });
        
        //$('.listing').parent().load('/trac/query?'+dataString+' .listing');
    }
    
    //hide update button
    $(":input[name='update']").hide();
    
    //load updated data after input change
    $(":input:not(select)").click(function() {
        update_filter();
    });

    $("input:text").change(function() {
        update_filter();
    });
    
    $("select").change(function() {
        //filter initial change event triggered by populating the the select elements
        if($(this).val() != "")
            update_filter();
    });
});