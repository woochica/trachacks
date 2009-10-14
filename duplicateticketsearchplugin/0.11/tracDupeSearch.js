$(document).ready(function() {
	$('div#content.ticket input#field-summary').blur(function() {
		var text = $('div#content.ticket input#field-summary').val();
		if (text.length > 0) {
			var xmlHref = location.href + '/../xmlrpc';
			
			var html = '<h5 class="loading">Loading related tickets..</h5>';
			var dupeticketlistDiv = $('div#content.ticket input#field-summary + div#dupeticketlist');
			if (dupeticketlistDiv.length == 0) {
				$('div#content.ticket input#field-summary').after('<div id="dupeticketlist" style="display:none;"></div>');
				dupeticketlistDiv = $('div#content.ticket input#field-summary + div#dupeticketlist');
			}
			$('ul',dupeticketlistDiv).slideUp('fast');
			dupeticketlistDiv.html(html).slideDown();
			
			$.ajax({
				url:xmlHref, 
				data:
					'<' +'?' + 'xml version="1.0"'+'?'+'><'+'methodCall>' + 
					'  <methodName>search.performSearch</methodName>' +
					'  <params><param><value>' + text + '</value></param>' +
					'  <param><array><data><value>ticket</value></data></array></param>' +
					'</params></methodCall>', 
				dataType:'xml', 
				type:'POST', 
				contentType:'text/xml',
				success: function(data, status) {
					var tickets = parseTracResponse(data);
					var ticketBaseHref = location.href + '/../ticket/';
					var searchBaseHref = location.href + '/../search?ticket=on&q=';
					var maxTickets = 15;
					
					var html = '';
					if (tickets === null) {
						// error
						dupeticketlistDiv.html('<h5 class="error">Error loading tickets.</h5>');
					} else if (tickets.length <= 0) {
						// no dupe tickets
						dupeticketlistDiv.hide();
					} else {
						html = '<h5>Possible related tickets:</h5><ul style="display:none;">'
						tickets = tickets.reverse();
						
						for (var i = 0; i < tickets.length && i < maxTickets; i++) {
							var ticket = tickets[i];
							html += '<li title="' + ticket.description + '"><a href="' + ticketBaseHref + ticket.ticket + '"><span class="' + ticket.status + '">#' + ticket.ticket + '</span></a>: ' +
							        ticket.type + ': ' + ticket.summary + '(' + ticket.status + (ticket.resolution ? ': ' + ticket.resolution : '') + ')' +
							        '</li>'
						}
						html += '</ul>';
						if (tickets.length > maxTickets) {
							var text = $('div#content.ticket input#field-summary').val();
							html += '<a href="' + searchBaseHref + escape(text) + '">More..</a>';
						}
						
						dupeticketlistDiv.html(html);
						$('> ul', dupeticketlistDiv).slideDown();
						
					}
					
				},
				error: function(xhr, textStatus, exception) {
					dupeticketlistDiv.html('<h5 class="error">Error loading tickets: ' + textStatus + '</h5>');
				}
			});
		}
	});
	
	function parseTracResponse(xmlData) {
		var returnData = new Array();
		var returnIdx = 0;
		
		var summaryRegex = /#(\d+)<\/span>:\s*([a-z0-9\-\_\ ]+):\s*(.*)\s*\(([a-z0-9\-\_\ ]+)(?:\: ([a-z0-9\-\_\ ]+))?\)$/i;
		
		//console.log('.each ', $('params > param > value > array > data > value', xmlData));
		var dataValues = $('params > param > value > array > data', xmlData);
		if (dataValues.length > 0) {
			$('> value',dataValues).each(function(i) {
				var xmlEntry = $(this);
				
				var url = xmlEntry.find('value:eq(0) string').text();
				var summaryRaw = xmlEntry.find('value:eq(1) string').text();
				var date = xmlEntry.find('value:eq(2) dateTime\\.iso8601').text();
				var owner = xmlEntry.find('value:eq(3) string').text();
				var descr = xmlEntry.find('value:eq(4) string').text();
				
				// filter for attachments
				if (url.indexOf('attachment/ticket') == -1) {
					
					var summaryMatches = summaryRegex.exec(summaryRaw);
					
					returnData[returnIdx++] = {
						url: url,
						summaryRaw: summaryRaw,
						date: date,
						owner: owner,
						description: descr,
						ticket: summaryMatches[1],
						type: summaryMatches[2],
						summary: summaryMatches[3],
						status: summaryMatches[4],
						resolution: summaryMatches[5]
					};
				}
				
			});
		} else {
			// didn't get a valid response at all
			return null;
		}
		//console.log(returnData);
		
		return returnData;
	}
});