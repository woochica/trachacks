function positionPopup(htmlText, coords) {
	$('popupDiv').innerHTML = htmlText;
	var offsetX = 0 - $('mapdata').scrollLeft;
	var offsetY = Element.getHeight($('top')) - $('mapdata').scrollTop;
	var y = parseFloat(coords[3]);
	var x = parseFloat(coords[0]);
	var midX = (pageWidth() / 2) - offsetX;
	var midY = (pageHeight() / 2) - offsetY;
	if (x > midX && y > midY) {
		//bottom right, place popup in top left
		x = parseFloat(coords[0]) - Element.getWidth($('popupDiv'));
		y = parseFloat(coords[1]) - Element.getHeight($('popupDiv')) - 45;
		$('popuptop').className = 'popuptop';
		$('popupbottom').className = 'popuptopleft';
	} else if (x > midX && y < midY) {
		//top right, place popup in the bottom left
		x = parseFloat(coords[0]) - Element.getWidth($('popupDiv'));
		$('popuptop').className = 'popupbottomleft';
		$('popupbottom').className = 'popupbottom';
	} else if (x < midX && y < midY) {
		//top left, place popup in the bottom right
		x = parseFloat(coords[2]);
		$('popuptop').className = 'popupbottomright';
		$('popupbottom').className = 'popupbottom';
	} else if (x < midX && y > midY) {
		//bottom left, place popup in the top right
		y = parseFloat(coords[1]) - Element.getHeight($('popupDiv')) - 45;
		x = parseFloat(coords[2]);
		$('popuptop').className = 'popuptop';
		$('popupbottom').className = 'popuptopright';
	}
	$('popupDiv').style.left = (x + offsetX) + 'px';
	$('popupDiv').style.top = (y + offsetY) + 'px';
	$('popupDiv').show();
}

var allowPopups = true;
function showPopup (node_title, coords) {
	if (allowPopups) {
		var popupRequest = new Ajax.Request(
			"mappopup",
			{
				method: 'get',
				parameters: 'node_title=' + node_title,
				onSuccess: function(transport) {
					positionPopup(transport.responseText, coords);
				}
			});
	}
}

// Creates the popup and adds mouseover events to the image map areas
// Also creates the search select box and adds nodes to it
function setPopups(referer) {
	var popup = Builder.node('div', {id:'popupDiv', className:'popupDiv'});
	$('mapdata').appendChild(popup);
	var searchBox = '<select id="searchSelectBox">'
	$('popupDiv').hide();
	map = $('mapdata').getElementsByTagName('area');
	//var map_array = $A(map);
	var offsetY = Element.getHeight($('top'));
	for (var i=0; i<map.length; i++) {
		Event.observe(map[i], 'mouseover', function(event) {
			var target = event.target || event.srcElement;
			var coords = $(target).coords.split(',');
			showPopup($(target).title, coords);
		});
		Event.observe(map[i], 'mouseout', function(event) {
			$('popupDiv').hide();
		});
		searchBox += '<option value="' + map[i].coords + '"';
		if ((referer == '/wiki/' + map[i].title) || (referer == '/milestone/' + map[i].title.escapeHTML()) || (referer == '/ticket/' + map[i].title.substring('{Ticket'.length, map[i].title.indexOf('|')))) {
			searchBox += ' selected';
		}
		searchBox += '>' + (map[i].title.indexOf('{Ticket')!=-1 ? map[i].title.substring(1, map[i].title.indexOf('|')) : map[i].title) + '</option>';
		//
	}
	$('searchBox').innerHTML = searchBox + '</select><input type="submit" value="Go To" onclick="gotoSelectedNode();"/>';
}
