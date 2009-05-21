map = null;

function map_locations(locations){
    
    if (map) {
        map.destroy();
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

    
    var options = { 
        //      units: "dd",  // only works in EPSG:4326
        maxExtent: bounds,
        maxResolution: 156543.03396025, // meters per pixel at maximum extent (world projection)
        projection: "EPSG:900913",  // use google's projection
    };
    
    // create a map opject with the options 
    map = new OpenLayers.Map('map', options);

    map_layers = layers();
    
    // layer for the marker point of interest
    var datalayer = new OpenLayers.Layer.Vector(
                                                "Data Layer",
                                                {});
    map_layers.push(datalayer);

    // add the layers to the map
    map.addLayers(map_layers);


    // 
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

    // add the point of interest to the data layer
      
    for (i in locations) {

        var point = new OpenLayers.Geometry.Point(locations[i]['longitude'], locations[i]['latitude']);
        var marker = new OpenLayers.Feature.Vector(point.transform(epsg4326, googleprojection), {content: locations[i].content});
        datalayer.addFeatures([marker]);
    }

    // zoom in on the point of interest
    map.zoomToExtent(datalayer.getDataExtent());
}
