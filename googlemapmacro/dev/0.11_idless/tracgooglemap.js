
// TODO: move this functions to an external file:

function SetMarkerByCoords(map,lat,lng,letter,link,title,target) {
    if (!title) { title = link; }
    var marker = new GMarker( new GLatLng(lat,lng),
        { title: title, icon: new GIcon (G_DEFAULT_ICON,
        'http://maps.google.com/mapfiles/marker'
        + letter + '.png') }
     );
    if (link) {
        GEvent.addListener(marker, "click", function() {
            if (target) {
                window.open(link);
            } else {
                window.location = link;
            }
        });
    }
    map.addOverlay(marker);
}

function SetMarkerByAddress(map,address,letter,link,title,target,geocoder) {
    if (!geocoder) {
        geocoder = new GClientGeocoder();
    }
    geocoder.getLatLng(
      address,
      function(point) {
        if (point) {
          SetMarkerByCoords(map, point.lat(), point.lng(), letter, link, title, target);
        }
      }
    )
}

// Array to store all Map init functions
var tracgooglemapfuncs = new Array();

function TracGoogleMap( initfunc, id ) {
    // 'id' is for future features and ignored at the moment
    tracgooglemapfuncs.push(initfunc);
};

$(document).ready( function () {
    if ( GBrowserIsCompatible() ) {
        // Go through all GoogleMap divs, set id and execute the 
        // associated init function:
        $("div.tracgooglemaps > div")
        .attr( 'id', function (index) {
            return 'tracgooglemap-' + index;
        })
        .each( function (index) {
            var initfunc = tracgooglemapfuncs[index];
            if (initfunc) {
                initfunc(this);
            }
        });
    }
});

$(window).unload( GUnload );

