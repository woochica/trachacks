function scrollup() { 
	var hoehe = (-1*document.getElementById("top1").offsetHeight 
        + document.getElementById("top3").offsetHeight)-50; 

	window.setTimeout('window.scrollBy(0, '+hoehe+')', 10);
}