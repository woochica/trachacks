/*
 * Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
	$(document).ready(function() {
		base = document.location.href.slice(0, 
				-document.location.pathname.length - document.location.search.length)
		       + $('link[rel="search"]').attr('href').slice(0, -7)
		$.plot($("#statushistorychart"), statushistorychart_data, {
			legend:{show : false},
			grid : {hoverable : true,
				    clickable : true},
			xaxis :{mode : "time"},
			yaxis :{max : statushistorychart_yaxis.length - 1,
				    tickFormatter : function(i, o) {return statushistorychart_yaxis[i]},
				    minTickSize : 1},
		});
		$("#statushistorychart").bind("plothover", function(event, pos, item) {
			if (item) {
				$("#statushistorychart_tooltip").remove();
				$('<div id="statushistorychart_tooltip">#' + item.series.label + '</div>').css({
					position : 'absolute',
					top : item.pageY - 30,
					left : item.pageX + 5,
					border : '1px solid #fdd',
					padding : '2px',
					'background-color' : '#fee',
				}).appendTo("body");
			} else {
				$("#statushistorychart_tooltip").remove();
			}
		});
		$("#statushistorychart").bind("plotclick", function(event, pos, item) {
			if (item) {
				location.href = base + "/ticket/" + item.series.label
			}
		});
	});
})(jQuery);