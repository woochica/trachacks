$(document).ready(function() {
	$('div#content.ticket input#field-summary').blur(function() {
		var text = $('div#content.ticket input#field-summary').val();
		if (text.length > 0) {
			var xmlHref = location.href + '/../xmlrpc';
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
					if (tickets.length > 0) {
						html = '<h5>Possible related tickets:</h5><ul>'
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
					}
					
					var existingDiv = $('div#content.ticket input#field-summary + div#dupeticketlist');
					if (existingDiv.length > 0) {
						existingDiv.html(html);
					} else {
						$('div#content.ticket input#field-summary').after('<div id="dupeticketlist">' + html + '</div>');
					}
				}
			});
		}
	});
	
	function parseTracResponse(xmlData) {
		var returnData = new Array();
		var returnIdx = 0;
		
		var summaryRegex = /#(\d+)<\/span>:\s*([a-z0-9\-\_\ ]+):\s*(.*)\s*\(([a-z0-9\-\_\ ]+)(?:\: ([a-z0-9\-\_\ ]+))?\)$/i;
		
		//console.log('.each ', $('params > param > value > array > data > value', xmlData));
		$('params > param > value > array > data > value', xmlData).each(function(i) {
			var xmlEntry = $(this);
			
			var url = xmlEntry.find('value:eq(0) string')[0].textContent;
			var summaryRaw = xmlEntry.find('value:eq(1) string')[0].textContent;
			var date = xmlEntry.find('value:eq(2) dateTime\\.iso8601')[0].textContent;
			var owner = xmlEntry.find('value:eq(3) string')[0].textContent;
			var descr = xmlEntry.find('value:eq(4) string')[0].textContent;
			
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
		//console.log(returnData);
		
		return returnData;
	}
});