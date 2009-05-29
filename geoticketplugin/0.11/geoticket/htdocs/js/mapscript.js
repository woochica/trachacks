maps = {};

function map_locations(locations, options) {

    // set default options
    if ( typeof(options) == 'undefined' ) {
        options = {};
    }
    defaults = {'zoom': false, 
                'id': 'map'}
    for ( var i in defaults ) {
        if ( typeof(options[i]) == 'undefined' ) {
            options[i] = defaults[i];
        }
    }

    // this is the projection where lon, lat work
    var epsg4326 = new OpenLayers.Projection("EPSG:4326");
    
    // this is google's projection
    var googleprojection = new OpenLayers.Projection("EPSG:900913");
  
    // bounds for google's projection == the whole world
    // units are in meters
    var bounds = new OpenLayers.Bounds(
                                       -2.003750834E7,-2.003750834E7,
                                       2.003750834E7,2.003750834E7);

    var map_options = { 
        //      units: "dd",  // only works in EPSG:4326
        maxExtent: bounds,
        maxResolution: 156543.03396025, // meters per pixel at maximum extent (world projection)
        projection: googleprojection,  // use google's projection
    };
    
    // create a map opject with the options
    var map = maps[options.id];
    if (!map) {
        map = new OpenLayers.Map('map', map_options);
        maps[options.id] = map;
        options.zoom = true;
    }
    if (map.layers.length == 0) {
        map.addLayers(layers());
    }    

    // layer for the marker points of interest
    var datalayer;
    if (map.getLayersByName('Data Layer').length == 0) {
        datalayer = new OpenLayers.Layer.Vector(
                                                "Data Layer",
                                                {});
        map.addLayer(datalayer);
    } else {
        datalayer = map.getLayersByName('Data Layer')[0];
        datalayer.removeFeatures(datalayer.features);
    }


    // add the data layer to the map
    map.addLayer(datalayer);


    // map controls
    if (map.getControlsByClass(OpenLayers.Control.SelectFeature).length == 0) {

        var selectfeature = new OpenLayers.Control.SelectFeature(datalayer);
        map.addControl(selectfeature);
        selectfeature.activate();

        var onPopupClose = function() { selectfeature.unselectAll(); }
	selectfeature.onSelect = function(feature){
            var content = feature.attributes.content;
            if ( content ) {
                var popup = new OpenLayers.Popup.FramedCloud("chicken",
                                                             feature.geometry.getBounds().getCenterLonLat(),
                                                             new OpenLayers.Size(100,100),
                                                             content,
                                                             null, true, onPopupClose);
                feature.popup = popup;
                map.addPopup(popup);
            }
	};

        selectfeature.onUnselect = function(feature){
            if (feature.popup) {
                map.removePopup(feature.popup);
                feature.popup.destroy();
                delete feature.popup;
            }
	};
    }

    // add the point of interest to the data layer
    for (var i in locations) {

        var point = new OpenLayers.Geometry.Point(locations[i]['longitude'], locations[i]['latitude']);
        var marker = new OpenLayers.Feature.Vector(point.transform(epsg4326, googleprojection), {content: locations[i].content});
        datalayer.addFeatures([marker]);
    }

    if (!locations || locations.length == 0) {
        // no data on the map, zoom to default view. 
        // TODO: add default Lon Lat to layers.html JS
        var bounds = new OpenLayers.Bounds();
        var min_lonlat = new OpenLayers.LonLat(min_lon,min_lat);
        var max_lonlat = new OpenLayers.LonLat(max_lon,max_lat);
        min_lonlat.transform(epsg4326, googleprojection);
        max_lonlat.transform(epsg4326, googleprojection);
        bounds.extend(min_lonlat);
        bounds.extend(max_lonlat);
        map.zoomToExtent(bounds);

    } else if ( options.zoom ) {

        // zoom in on the points of interest
        map.zoomToExtent(datalayer.getDataExtent());
    }
}
