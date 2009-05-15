$(document).ready(function() {
        var locationnode = $("#field-location");
        $("ul.geolocation_error a").click(function() {
                locationnode.val($(this).text());
                return false;
            });
    });