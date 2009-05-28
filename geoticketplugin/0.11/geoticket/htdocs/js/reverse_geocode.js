$(document).ready(function() {

	map.events.register("click", map, function(e){	
		var lonlat = map.getLonLatFromViewPortPx(e.xy);
		lonlat.transform(map.getProjectionObject(), new OpenLayers.Projection('EPSG:4326'));
		var loc = {
			latitude: lonlat.lat,
			longitude: lonlat.lon,
		};
		map_locations([loc], false);
		getAddress(lonlat); 
	 });


	function getAddress(lonlat) { 
	    var lat = lonlat.lat; 
	    var lon = lonlat.lon; 

            // XXX this will need to change
            var url = "geocode.php?lat=" + lat + "&lon=" + lon;	
            
            $.ajax({
                    url: url,
                        cache: false,
                        success: function(data){
		  	$('#field-location').val(data);
                    }
		});

	  }

 })