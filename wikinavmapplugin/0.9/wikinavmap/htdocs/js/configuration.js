var configured = false;
function setConfiguration() {
	if (!configured) {
		setSliders();
		var overlay = Builder.node('div', {id:'overlay', style:'position:absolute;background-color:#000;display:none;zIndex:9998;'});
		$('main').appendChild(overlay);
		configured = true;
	}
	//generateColours();
}

function showModal(containerDiv) {
	modal = true;
	var container = $(containerDiv);
	var overlay = $('overlay');
	var x = (pageWidth()/2) - (container.getWidth()/2);
	var y = (pageHeight()/2) - (container.getHeight()/2);
	container.setStyle({
		top: y+'px',
		left: x + 'px',
		zIndex: 9999
	});
	overlay.setStyle({
		left: "0px",
		top: "0px",
		width: pageWidth() + "px",
		height: document.body.scrollHeight + "px"
	});
	new Effect.Appear('overlay', {from:0, to:0.3, duration:0.5});
	new Effect.Appear(containerDiv, {duration:0.5});
}

function hideModal(containerDiv) {
	modal = false;
	new Effect.Fade('overlay', {duration:0.5});
	new Effect.Fade(containerDiv, {duration:0.5});
}

var slider;
function setSliders() {
	slider = new Control.Slider('colour_slider','colour_track',{range:$R(1,5),
	    values:[1,2,3,4,5]});

	// Setting the callbacks later on
	slider.options.onChange = function(value){
	    COLOUR_COUNT = value;
		generateColours();
		setDates();
	};
	slider.options.onSlide = function(value){                                  
	    $('colour_no').innerHTML = value + (value==1?" Colour":" Colours");
	};
	slider.setValue(5);
}

//Setup Colour Key	
function DateToString(date) {
	//converts dates to the format DD/MM/YYYY
	var day = date.getDate()<10 ? "0" + date.getDate() : date.getDate();
	var month = (date.getMonth()+1)<10 ? "0" + (date.getMonth()+1) : date.getMonth()+1;
	var year = date.getFullYear().toString();
	return day + '/' + month + '/' + year;
}

function StringToDate(str) {
	//Parses dates form the format DD/MM/YYYY
	var regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
	return new Date(str.replace(regex, '$2/$1/$3'));
}

function StringToElapsed(str) {
	//Converts a string DD/MM/YYYY to the amount of time elapsed in days, weeks and months
	var date = StringToDate(str);
	if (date.getTime()<0) return "ever";
	var today = new Date();
	var one_day = 1000*60*60*24;
	var days_old = ((today.getTime() - date.getTime())/one_day);
	if (days_old<=0) return "today"
	if (days_old<=1) return "yesterday"
	days_old = days_old - (days_old % 1);
	var years_old = (days_old/365) - (days_old/365 % 1);
	days_old = days_old % 365;
	var months_old = (days_old/30) - (days_old/30 % 1);
	days_old = days_old % 30;
	var weeks_old = (days_old/7) - (days_old/7 % 1);
	days_old = days_old % 7;
	//var elapsed = "older than ";
	var elapsed = years_old ? years_old + (years_old > 1 ? " years " : " year ") : "";
	elapsed += months_old ? months_old + (months_old > 1 ? " months " : " month ") : ""; 
	elapsed += weeks_old ? weeks_old + (weeks_old > 1 ? " weeks " : " week ") : "";
	elapsed += days_old ? days_old + (days_old > 1 ? " days " : " day ") : "";
	return elapsed;
}


function setDates(dates) {
	var date_array = new Array();
	if (!dates) {
		date = new Date();
		date.setDate(date.getDate()+1); //set to start as tomorrow by default
		var one_day = 1000*60*60*24;
		date_array.push(DateToString(date));
		date.setTime(date.getTime()-one_day); //yesterday
		date_array.push(DateToString(date));
		date.setTime(date.getTime()-(7*one_day)); //week ago
		date_array.push(DateToString(date));
		date.setTime(date.getTime() - (23*one_day)); //month ago (approx 30 days)
		date_array.push(DateToString(date));
		date.setTime(date.getTime()-(335*one_day)); //1 year ago (approx 365 days)
		date_array.push(DateToString(date));
		date.setTime(0); //ever ago
		date_array.push(DateToString(date));
	} else {
		date_array = dates.split(',');
		//date_array = date_array.invoke('escapeHTML');
	}
	var inputs = $('colour_form').getElementsByTagName('input');
	for (var i=0; i < (COLOUR_COUNT+1); i++) {
		if (i >= date_array.length) {
			inputs[i].value = '01/01/1970';
		} else {
			inputs[i].value = date_array[i].unescapeHTML();	
		}
	}
	calculateTimes();
}

function showDates() {
	var dates = $('colour_form').getElementsByClassName('datetd');
	var showdates = $('showdates');
	if (showdates.innerHTML == 'show dates') {
		showdates.innerHTML = 'hide dates';
		dates.each(function(date) {
			date.show();
		});
	} else {
		showdates.innerHTML = 'show dates';
		dates.each(function(date) {
			date.hide();
		});
	}
}


function validateDates() {
	var valid = true;
	var later_date;
	var inputs = $('colour_form').getElementsByTagName('input');
	$A(inputs).each(function(input) {
		var v = input.value;
		var regex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
		var d = new Date(v.replace(regex, '$2/$1/$3'));
		if (d.getTime()<0) return;
		if (( parseInt(RegExp.$2, 10) != (1+d.getMonth()) ) || (parseInt(RegExp.$1, 10) != d.getDate()) || (parseInt(RegExp.$3, 10) != d.getFullYear() )) {
			$('date_err').innerHTML = v + " is not a valid date. Please use the format DD/MM/YYYY";
			$('date_err').show();
			valid = false;
			return;
		}
		if (later_date && (later_date <= d)) {
			$('date_err').innerHTML = v + " is not a valid date. It must come before " + DateToString(later_date);
			$('date_err').show();
			//input.parent.show();
			valid = false;
			return;
		}
		later_date = d;
	});
	if (valid) {
		$('date_err').hide();
	}
	return valid;
}

function setColours(base_colour) {
//	if (no_colours) {
//		COLOUR_COUNT = no_colours;
//	}
	var regex = /^\#(\w\w)(\w\w)(\w\w)$/
	var r = parseInt(base_colour.replace(regex, '$1'), 16);
	var g = parseInt(base_colour.replace(regex, '$2'), 16);
	var b = parseInt(base_colour.replace(regex, '$3'), 16);
	var increment = Math.round((255 - Math.min(r,g,b))/COLOUR_COUNT);
	colours = [];
	//generate colours
	for (var i=0; i< COLOUR_COUNT; i++) {				
		colours.push(hex(r) + hex(g) + hex(b));
		r<255?(r+increment)>255?r=255:r+=increment:r=255;
		g<255?(g+increment)>255?g=255:g+=increment:g=255;
		b<255?(b+increment)>255?b=255:b+=increment:b=255;				
	}
	var configColours = $('colour_form').getElementsByClassName('colourtd');
	var keyColours = $('colour_key_top').getElementsByClassName('colourtd');
	for (var i=0; i<configColours.length; i++) {
		configColours[i].setStyle({backgroundColor: "#"+colours[i], color:"#FFFFFF"});
		keyColours[i].setStyle({backgroundColor: "#"+colours[i], color:"#FFFFFF"});
	}
}


function hex(c){return c.toString(16).length<2?"0"+c.toString(16):c.toString(16)}
var colours;
var COLOUR_COUNT = 5;
function generateColours() {
	var configString = '';
	var keyString = '';
	for (var i=0; i<= COLOUR_COUNT; i++) {
		configString += '<td id="date' + i + '" style="' + ($('showdates').innerHTML=="show dates"?'display:none;':'display:block') + '" class="datetd">DD/MM/YYYY<br/><input type="text" id="input' + i + '" name="date' + i + '" size="9" value="10/04/2007" /></td>';
		if (i<COLOUR_COUNT) {
			configString += '<td id="colour' + i + '" class="colourtd"></td>';
			keyString += '<td id="colour' + i + '" class="colourtd"></td>';
		}
	}
	$('colour_form').innerHTML = "<table><tr>" + configString + "</tr></table>";
	$('colour_key_top').innerHTML = "<table><tr>" + keyString + "</tr></table>";
	setColours($('base_colour').value);
	//var tomorrow = new Date();
	//tomorrow.setDate(tomorrow.getDate()+1);
	//setDates(tomorrow);
	Form.getElements($('colour_form')).each(function(input) {
		Event.observe(input, 'blur', calculateTimes);
	});
	//$('colour_key2').innerHTML = $('colour_key').innerHTML;
}

function calculateTimes(ev) {
	var inputs = $('colour_form').getElementsByTagName('input');
	var configColours = $('colour_form').getElementsByClassName('colourtd');
	var keyColours = $('colour_key_top').getElementsByClassName('colourtd');
	
	if (validateDates()) {
		for (var i=0; i < COLOUR_COUNT; i++) {
			var from = StringToElapsed(inputs[i].value);
			var to = StringToElapsed(inputs[i+1].value);
			configColours[i].innerHTML = from + (to=="yesterday"?"":" to " + StringToElapsed(inputs[i+1].value) + " ago");
			keyColours[i].innerHTML = from + (to=="yesterday"?"":" to " + StringToElapsed(inputs[i+1].value) + " ago");
		}
	}
}
