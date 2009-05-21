location_error = false;

function location_filler() {
    var locationnode = $("#field-location");
    $("ul.geolocation_error a").click(function() {
            locationnode.val($(this).text());
            var href = $.query($(this).attr('href'));
            map_locations([href]);
            if ( location_error ) {
                $("#warning").remove();
            }
            return false;
        });
}

$(document).ready(location_filler);

$(document).ready(function() {

$("#field-location").change(function() {

var url = geolocator_url + "?location=" + escape($(this).val());

if(location_error)
{
  $("#warning").remove();
}

$.getJSON(url, function(locations) {
if ( locations.error )
{
  location_error = true;
  $("#ctxtnav").after('<div id="warning" class="system-message"><strong>Warning: </strong> ' + locations.error + '</div>');
  location_filler();
}
else
{

 map_locations(locations.locations);
}
});
});
});

