$(document).ready(function() {
	var tracBase = getTracBaseUrl();
	//console.log('tracBase = ', tracBase);
		
	var xmlHref = tracBase.url + 'xmlrpc';
	
	$('div#content.ticket input#field-summary').blur(function() {
		var text = $('div#content.ticket input#field-summary').val();
		if (text.length > 0) {
			
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
					var tickets = parseTracResponse(data, tracBase.ticket);
					var ticketBaseHref = tracBase.url + 'ticket/';
					var searchBaseHref = tracBase.url + 'search?ticket=on&q=';
					var maxTickets = 15;
					
					var html = '';
					if (tickets === null) {
						// error
						dupeticketlistDiv.html('<h5 class="error">Error loading tickets.</h5>');
					} else if (tickets.length <= 0) {
						// no dupe tickets
						dupeticketlistDiv.slideUp();
					} else {
						html = '<h5>Possible related tickets:</h5><ul style="display:none;">'
						tickets = tickets.reverse();
						
						for (var i = 0; i < tickets.length && i < maxTickets; i++) {
							var ticket = tickets[i];
							html += '<li title="' + htmlencode(ticket.description) +
								    '"><a href="' + ticketBaseHref + ticket.ticket +
								    '"><span class="' + htmlencode(ticket.status) + '">#' +
								    ticket.ticket + '</span></a>: ' + htmlencode(ticket.type) + ': ' +
								    htmlencode(ticket.summary) + '(' + htmlencode(ticket.status) +
								    (ticket.resolution ? ': ' + htmlencode(ticket.resolution) : '') +
								    ')' + '</li>'
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
	
	function htmlencode(text) {
		return $('<div/>').text(text).html().replace(/"/g, '&quot;').replace(/'/g, '&apos;');
	}
	
	function getTracBaseUrl() {
		// returns the base URL to trac, based on guesses. This would be better with trac templating 
		var returnVal = { url:null, ticket:null };
		var urlRegex = /^.+?(?=\/newticket.*|\/ticket\/(\d+).*|\/ticket.*)/i;
		var match = urlRegex.exec(location.href);
		if (match) {
			if (match[1]) { 
				// also have a ticket number 
				returnVal.ticket = match[1];
			}
			returnVal.url = match[0] + (match[0].match('/$') ? '' : '/');
		} else {
			returnVal.url = location.href + (location.href.match('/$') ? '' : '/') + '../';
		}
		return returnVal;
	}
	
	function parseTracResponse(xmlData, currentTicketId) {
		var returnData = new Array();
		var returnIdx = 0;
		
		var summaryRegex = /#(\d+)<\/span>:\s*(.*):\s*(.*)\s*\(([^:.]*)(?:\: (.*))?\)$/i;
		
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
					
					// skip current ticket
					if (summaryMatches[1] != currentTicketId) {
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
