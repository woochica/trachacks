function query_location_filler() {
    var locationnode = $("#center-location");
    $("ul.geolocation_error a").click(function() {
            locationnode.val($(this).text());
            var href = $.query($(this).attr('href'));
            $("#warning").remove();
            return false;
        });
}

$(document).ready(query_location_filler);