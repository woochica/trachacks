/* 
	requires jquery
*/


/* initialize globally for faster access */
if(document.getElementById){
	ppconnect = document.getElementById('ppconnect');
	ppconnect_from = document.getElementById('ppconnect_from');
	ppconnect_to = document.getElementById('ppconnect_to');
}
ppsavedivid = 'ppconnect_save';

function ppconnecttickets(ticketid){
	if( ppconnecttickets_get_from() == '' ) {
		ppconnecttickets_set_from(ticketid);
	} else {
		/* obey cycles */
		if( ppconnecttickets_get_from() == ticketid ){
			ppconnecttickets_set_from('');
			ppconnecttickets_render_reset();
			return false;
		} else  {
			ppconnecttickets_set_to(ticketid);
			ppconnecttickets_request();
		}
	}
	ppconnecttickets_render();
	return false;
}

function ppconnecttickets_get_from(ticketid){
	return(ppconnect_from.innerHTML);
}

function ppconnecttickets_set_from(ticketid){
	ppconnect_from.innerHTML = ticketid;
}

function ppconnecttickets_get_to(ticketid){
	return(ppconnect_to.innerHTML);
}

function ppconnecttickets_set_to(ticketid){
	ppconnect_to.innerHTML = ticketid;
}

function ppconnecttickets_render_reset(){
	ppconnect.innerHTML = '';
	hideIfShown();
}

function ppconnecttickets_render(){
	showIfHidden();
	ppconnect.innerHTML = '';
	if( ppconnecttickets_get_from() != "" ){
		ppconnect.innerHTML += '<span id="ppconnect_descr">ticket dependencies add or remove:</span> ticket #'+ppconnecttickets_get_from()+' depends on ';
	}
	if( ppconnecttickets_get_to() != "" ){
		ppconnect.innerHTML += ' ticket #'+ppconnecttickets_get_to();
		ppconnect.innerHTML += '<div id="ppsavedivid">loading</div>';
	} else {
		ppconnect.innerHTML += ' ... (hit connector of successor ticket)';
	}
}

/**
 * save new dependencies, thereafter reload page
 */
function ppconnecttickets_request(){
	ppconnecttickets_render();
	// TODO: make configurable
	myurl = $("#mainnav a").attr("href");
	myurl = myurl.split('/wiki')[0]+"/pp_ticket_changes/?ppdep_from="+ppconnecttickets_get_from()+"&ppdep_to="+ppconnecttickets_get_to();
	$.ajax({
		url: myurl,
		cache: false,
		success: function(html){
			$("#ppsavedivid").empty().append('<div>reloading this page ...</div>');
			ppconnecttickets_reload();
		},
		error: function(html){
			$("#ppsavedivid").empty().append('An error occurs, while <a href="'+myurl+'">calling the ticket changer</a> remotely.');
		}
	});
}
	
function ppconnecttickets_reload(){
	mysearch = window.location.search;
	mysearch = mysearch.replace(/ppdep_from=\d+&ppdep_to=\d+/gi, ''); // delete old values
// 	mysearch = mysearch.replace(/&&+/gi, '&'); // delete duplicates
	mysearch +="&ppdep_from="+ppconnecttickets_get_from()+"&ppdep_to="+ppconnecttickets_get_to();
	window.location.search = mysearch;
}

function showIfHidden(){
// 	showandhidePermanent(ppconnect, 1);
// 	$(ppconnect).show("fast");
	$(ppconnect).slideDown("fast");
}

function hideIfShown(){
// 	showandhidePermanent(ppconnect, 0);
// 	$(ppconnect).hide("slow");
	$(ppconnect).slideUp("slow");
}

// function showandhidePermanent(elem, state) {
// 	if( 1 == state  ) 
// 	{
// 		elem.style.display = "block";
// 	}
// 	else 
// 	{ 		
// 		elem.style.display = "none";
// 	}
// }

$(document).ready(function () {
	$(".project_image .ticket_inner a").tooltip({
 		bodyHandler: function() { 
 			$("#tooltip").load(this.href+" #ticket");
 			this.title = ""
 			return ""; 
 		}, 
		track: false, 
		delay: 0, 
		showURL: true, 
		opacity: 1, 
		fixPNG: true, 
		showBody: " - ", 
// 		extraClass: "pretty fancy", 
 		extraClass: "tooltip2", 
		showURL: true
	});
	// remove all title values
//  	$(".project_image .ticket_inner a").each(function() { this.title = "";});
});


