location_error = false;
warnings = [];

function location_filler() {
    var locationnode = $("#field-location");
    $("ul.geolocation_error a").click(function() {
            locationnode.val($(this).text());
            var href = $.query($(this).attr('href'));
            $('#latitude').remove();
            $('#longitude').remove();
            $('#propertyform').append('<input name="latitude" id="latitude" type="hidden" value="' + href.latitude + '"/>');
            $('#propertyform').append('<input name="longitude" id="longitude" type="hidden" value="' + href.longitude + '"/>');
            
            map_locations([href], {zoom: true});
            if ( location_error ) {
                $("#warning").remove();
                if ( warnings.length )
                    {
                        warning_string = '<div id="warning" class="system-message"><strong>Warning: </strong>';
                        if ( warnings.length == 1 ) {
                            warning_string += warnings[0] + '</div>';
                        }
                        else {
                            warning_string += '<ul>';
                            for ( warning in warnings ) {
                                warning_string += '<li>' + warning + '</li>';
                            }
                            warning_string += '</ul></div>';
                        }
                        $("#content").before(warning_string);
                    }
            }
            return false;
        });
}

$(document).ready(location_filler);

$(document).ready(function() {
        
        $("#field-location").change(function() {
                
                var url = geolocator_url + "?location=" + escape($(this).val());
                if(location_error) {
                    $("#warning").remove();
                }

                $.getJSON(url, function(locations) {
                        $('#latitude').remove();
                        $('#longitude').remove();
                        if ( locations.error )
                            {
                                location_error = true;
                                if ( warnings.length ) {
                                    var warning_string = '<div id="warning" class="system-message"><strong>Warning: </strong> <ul><li>' + locations.error + '</li>';
                                    for ( warning in warnings)
                                        {
                                            warning_string += '<li>' + warnings[warning] + '</li>';
                                        }
                                    $("#content").before(warning_string + '</ul></div>');
                                }
                                else {
                                    $("#content").before('<div id="warning" class="system-message"><strong>Warning: </strong> ' + locations.error + '</div>');
                                }
                                location_filler();
                            }
                        else
                            {
                                
                                $('#propertyform').append('<input name="latitude" id="latitude" type="hidden" value="' + locations.locations[0].latitude + '"/>');
                                $('#propertyform').append('<input name="longitude" id="longitude" type="hidden" value="' + locations.locations[0].longitude + '"/>');
                                $('#field-location').val(locations.locations[0].address);
                                map_locations(locations.locations, {zoom: true});
                            }
                    });
            });
    });

$(document).ready(function() {
        var warning_text = 'Multiple locations found';
        elements = $("#warning:contains('Multiple locations found')");
        if ( elements.length ) {
            $("#warning ul li").each(function() {
                    text = $(this).text();
                    if ( text.indexOf(warning_text) == -1 ) {
                        warnings.push(text);
                    }
                });
            location_error = true;
            $("#field-location").change();
        }
    })
