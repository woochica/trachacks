function location_filler() {
    var locationnode = $("#field-location");
    $("ul.geolocation_error a").click(function() {
            locationnode.val($(this).text());
            var href = $.query($(this).attr('href')); 
            return false;
        });
}

$(document).ready(location_filler);