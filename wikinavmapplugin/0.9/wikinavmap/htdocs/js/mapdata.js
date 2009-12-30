function pageWidth() {
	return window.innerWidth != null? window.innerWidth : document.documentElement && document.documentElement.clientWidth ?       document.documentElement.clientWidth : document.body != null ? document.body.clientWidth : null;
}
 
function pageHeight() {
	return  window.innerHeight != null? window.innerHeight : document.documentElement && document.documentElement.clientHeight ?  document.documentElement.clientHeight : document.body != null? document.body.clientHeight : null;
}

function documentHeight() {
	Math.max(pageHeight(), document.body.scrollHeight());
}

function documentWidth() {
	Math.max(pageWidth(), document.body.scrollWidth());
}

function loadMapData (obj_id, referer, loading) {
	var url = 'mapdata?referer=' + referer + '&' + Form.serialize('colour_form') + '&' + Form.serialize('filter_form') + '&colours=' + colours.flatten() + '&colour_count='+COLOUR_COUNT;
	var linkhere = 'navmap?referer=' + referer + '&' + Form.serialize('colour_form') + '&' + Form.serialize('filter_form') + '&base_colour=' + $('base_colour').options[$('base_colour').selectedIndex].text + '&colour_no=' + slider.value;
	$('linkhere').href = linkhere;
	var filter_description = "for " + ($('show_tickets').checked ? ($('ticket_filter').value.indexOf('user') > -1 ? $('ticket_filter').options[$('ticket_filter').selectedIndex].text.replace('...', $('t_username').value) : $('ticket_filter').options[$('ticket_filter').selectedIndex].text) : "") +
							($('show_tickets').checked && $('show_wiki').checked ? " and " : " ") + ($('show_wiki').checked ? ($('wiki_filter').value == 'user' ? $('wiki_filter').options[$('wiki_filter').selectedIndex].text.replace('...',$('w_username').value) : $('wiki_filter').options[$('wiki_filter').selectedIndex].text) : "")
	$('filter_description').innerHTML = filter_description;
	if (validateDates()) {
		if (modal) {hideModal('configure_window');}
		setDimensions();
		var loading = Builder.node('div', {id:'loading', style:'position:absolute;width:100px;'}, [
		Builder.node('img', {id:'loadingImg', src:loading, align:'center'})
		]);
		$('mapdata').appendChild(loading);
		loading.style.top = (pageHeight()/3) + 'px';
		loading.style.left = (pageWidth()/2) + 'px';
		var mapRequest = new Ajax.Request(
			url,
			{
				method: 'get',
				onSuccess: function(transport) {
					$(obj_id).innerHTML = transport.responseText;
					overview_done = false;
					createOverviewImage();
					//alert('success');
					setPopups(referer);
					//gotoSelectedNode();
					//setConfiguration();
					new DragScrollable('mapdata');
					$('mapdata').scrollLeft = 0;
					$('mapdata').scrollTop = 0;
				},
				onFailure: function(transport) {
					$(obj_id).innerHTML = '<strong>loading failed</strong><br/>' + url;
				}
			});
	}
}

var modal = false;
var overview_done = false;
function setDimensions() {
	$('mapdata').setStyle({
		width: (pageWidth()-30) + "px",
		height: (pageHeight()-$('top').getHeight() - $('banner').getHeight() - $('mainnav').getHeight() - 30) + "px"
	});
	if (overview_done) {
		posOverviewImage();
	}
	if (modal) {
		var overlay = $('overlay');
		overlay.setStyle({
			left: "0px",
			top: "0px",
			width: pageWidth() + "px",
			height: pageHeight() + "px"
		});
	}
}

var overviewDiv;
var overviewScale;
function createOverviewImage() {
	var map_image = $($('mapdata').getElementsByTagName('img')[0]);
	var o_width = '150px';
	if (map_image.getWidth() == 0) {
		//Image hasn't loaded yet, wait 1 second and try again
		new PeriodicalExecuter(function(pe) {
			pe.stop();
			createOverviewImage();
		}, 1);
		return;
	}
	if (overview_done) return;
	overview_done = true;
	overviewScale = 150/map_image.getWidth(); 
	//alert('scale ' + overviewScale);
	var o_height = (overviewScale * map_image.height) + 'px';
	overviewDiv = Builder.node('div', {id:'overviewDiv', style:'border: 1px solid #B41A1A; position:absolute;'},[
	Builder.node('img', {id:'overviewImage', src:map_image.src,border:'1px white',width:o_width,height:o_height}),
	Builder.node('div', {id:'overviewLocation', style:'border: 1px dashed black; background-color:blue; opacity:0.2; filter: alpha(opacity=20); position:absolute;'})
	]);
	$('mapdata').appendChild(overviewDiv);
	new Draggable('overviewLocation', {snap: function(x,y){
		var element_dim = $('overviewLocation').getDimensions();
		var parent_dim = $('overviewDiv').getDimensions();
		var xMin = 0;
		var xMax = parent_dim.width - element_dim.width;
		var yMin = 0;
		var yMax = parent_dim.height - element_dim.height;
		x = x < xMin ? xMin : x;
		x = x > xMax ? xMax : x;
		y = y < yMin ? yMin : y;
		y = y > yMax ? yMax : y;
		return [x,y];
	}, onEnd:scrollOverview}); 
	posOverviewImage();
};

function scrollOverview(draggable) {
	var element = draggable.element;
	var scrollLeft = parseFloat(element.style.left) / overviewScale;
	var scrollTop = parseFloat(element.style.top) / overviewScale;
	$('mapdata').scrollLeft = scrollLeft;
	$('mapdata').scrollTop = scrollTop;
	/*
	if ($('mapdata').scrollLeft > scrollLeft) {
		new PeriodicalExecuter(function(pe) {
			if ($('mapdata').scrollLeft > scrollLeft) {
				$('mapdata').scrollLeft-=10;
			} else {
				$('mapdata').scrollLeft = scrollLeft;
				pe.stop();
			}
		}, 0.01);
	} else if ($('mapdata').scrollLeft < scrollLeft) {
		new PeriodicalExecuter(function(pe) {
			if ($('mapdata').scrollLeft < scrollLeft) {
				$('mapdata').scrollLeft+=10;
			} else {
				$('mapdata').scrollLeft = scrollLeft;
				pe.stop();
			}
		}, 0.01);
	}
	if ($('mapdata').scrollTop > scrollTop) {
		new PeriodicalExecuter(function(pe) {
			if ($('mapdata').scrollTop > scrollTop) {
				$('mapdata').scrollTop-=10;
			} else {
				$('mapdata').scrollTop = scrollTop;
				pe.stop();
			}
		}, 0.01);
	} else if ($('mapdata').scrollTop < scrollTop) {
		new PeriodicalExecuter(function(pe) {
			if ($('mapdata').scrollTop < scrollTop) {
				$('mapdata').scrollTop+=10;
			} else {
				$('mapdata').scrollTop = scrollTop;
				pe.stop();
			}
		}, 0.01);
	}*/
};

function posOverviewImage() {
	var posX = Element.getWidth($('mapdata')) - Element.getWidth($('overviewDiv')); //getposOffset($('mapdata'), 'left') + Element.getWidth($('mapdata')) - Element.getWidth(overviewDiv) - 10;
	var posY = Element.getHeight($('top')); //getposOffset($('mapdata'), 'top') - 98;
	overviewDiv.setStyle({
		left: posX + 'px',
		top: posY + 'px'
	});
	posOverviewLocation();
};

function posOverviewLocation() {
	//var overviewScale = 150/map_image.getWidth(); 
	//alert(overviewScale);
	$('overviewLocation').setStyle({
		width: Math.min($('mapdata').getWidth() * overviewScale, overviewDiv.getWidth()) + 'px',
		height: Math.min($('mapdata').getHeight() * overviewScale, overviewDiv.getHeight()) + 'px',
		left: $('mapdata').scrollLeft * overviewScale + 'px',
		top: $('mapdata').scrollTop * overviewScale + 'px'
	});
	//alert(($('mapdata').scrollLeft * overviewScale) + " " + ($('mapdata').scrollTop * overviewScale));
};

function toggleOverview(link_obj) {
	Effect.toggle(overviewDiv, 'slide', {duration:0.5});
	if (link_obj.innerHTML == "show overview") {
		link_obj.innerHTML = "hide overview";
	} else {
		link_obj.innerHTML = "show overview";
	}
};

function gotoSelectedNode () {
	var selected = $('searchSelectBox');
	var node_title = selected.options[selected.selectedIndex].text;
	var coords = selected.options[selected.selectedIndex].value.split(',');
	var map_dim = $('mapdata').getDimensions();
	// Place the node in the centre of the map
	$('mapdata').scrollLeft = coords[0] - (map_dim.width / 3);
	$('mapdata').scrollTop = coords[1] - (map_dim.height / 3);
	posOverviewLocation();
	showPopup(node_title, coords);
}

/*
* Drag Scollable taken from http://wiki.script.aculo.us/scriptaculous/show/DragScrollable
* Modified by Adam Ullman for use in WikiNavMap
*/
var DragScrollable = Class.create();
DragScrollable.prototype = {
  initialize: function(element) {
    this.element = $(element);
    this.active = false;
    this.scrolling = false;

    this.element.style.cursor = 'move';

    this.eventMouseDown = this.startScroll.bindAsEventListener(this);
    this.eventMouseUp   = this.endScroll.bindAsEventListener(this);
    this.eventMouseMove = this.scroll.bindAsEventListener(this);

    Event.observe(this.element, 'mousedown', this.eventMouseDown);
  },
  destroy: function() {
    Event.stopObserving(this.element, 'mousedown', this.eventMouseDown);
    Event.stopObserving(document, 'mouseup', this.eventMouseUp);
    Event.stopObserving(document, 'mousemove', this.eventMouseMove);
  },
  startScroll: function(event) {
	allowPopups = false;
    this.startX = Event.pointerX(event);
    this.startY = Event.pointerY(event);
    if (Event.isLeftClick(event) &&
        (this.startX < this.element.offsetLeft + this.element.clientWidth) &&
        (this.startY < this.element.offsetTop + this.element.clientHeight)) {
      this.element.style.cursor = 'move';
      Event.observe(document, 'mouseup', this.eventMouseUp);
      Event.observe(document, 'mousemove', this.eventMouseMove);
      this.active = true;
      Event.stop(event);
    }
  },
  endScroll: function(event) {
	allowPopups = true;
    this.element.style.cursor = 'move';
    this.active = false;
    Event.stopObserving(document, 'mouseup', this.eventMouseUp);
    Event.stopObserving(document, 'mousemove', this.eventMouseMove);
    Event.stop(event);
	posOverviewLocation();
  },
  scroll: function(event) {
    if (this.active) {
      this.element.scrollTop += (this.startY - Event.pointerY(event));
      this.element.scrollLeft += (this.startX - Event.pointerX(event));
      this.startX = Event.pointerX(event);
      this.startY = Event.pointerY(event);
    }
    Event.stop(event);
	posOverviewLocation();
  }
}
