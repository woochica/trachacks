function getAddress(lonlat) { 
    var lat = lonlat.lat; 
    var lon = lonlat.lon; 
    
    // XXX this will need to change
    var url = reverse_geolocator_url + "?latitude=" + lat + "&longitude=" + lon;	
    
    $.getJSON(url, function(data){
            $('#field-location').val(data.location.address);
            $('#latitude').remove();
            $('#longitude').remove();
            $('#propertyform').append('<input name="latitude" id="latitude" type="hidden" value="' + lat + '"/>');
            $('#propertyform').append('<input name="longitude" id="longitude" type="hidden" value="' + lon + '"/>');
            
        });
}

$(document).ready(function() {
        var map = maps['map'];
        if ( map ) {
            
            map.events.register("click", map, function(e){	
                    var lonlat = map.getLonLatFromViewPortPx(e.xy);
                    lonlat.transform(map.getProjectionObject(), new OpenLayers.Projection('EPSG:4326'));
                    var loc = {
                        latitude: lonlat.lat,
                        longitude: lonlat.lon,
                    };
                    map_locations([loc], {'zoom': false});
                    getAddress(lonlat); 
                });
        }
    })