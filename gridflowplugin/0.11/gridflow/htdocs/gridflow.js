/* 
 * Javascript component for GridFlow Plugin.
 * dgc@uchicago.edu
 *
 * Modelled very loosely on GridMod by trac-dev@abbywinters.com.
 *
 * This Trac plugin is derived from other Trac components plus
 * original code.
 *
 * This code was inspired by Zach Miller's Gridmodify plugin, which is
 * marked as 'Copyright (c) 2008 Zach Miller and Abbywinters.com.' Most
 * of that code was actually copied verbatim from Trac itself, so I do
 * not believe that any abbywinters.com copyright claim would be valid
 * for this product. However, if this proves incorrect, I will gladly
 * update the copyright notice or change the code.
 */

if (!window.console)
	window.console = {};
if (!window.console.firebug || !window.console.log) {
	var log = document.createElement('code');
	var divs = document.getElementsByTagName('div');
	log.innerHTML = '<h3>Log:</h3>';
	window.console.log = function (msg) { log.innerHTML += msg + '<br/>\n'; };
}

// I don't know jQuery, so here's some plain, boring Javascript.
// Yes yes, I am as a leper unto the cleansed.
function gridflow_init () {
	if (log) {
		var body = document.getElementsByTagName('body')[0];
		body.appendChild(log);
	}

	// Build list of tables to mess with
	var targets = new Array();
	var tables = document.getElementsByTagName('table');
	for (i = 0; i < tables.length; i++) {
		if (tables[i].className == 'listing tickets') {
			targets.push(tables[i]);
		}
	}


	// Add 'triage' header to target tables only
	for (i = 0; i < targets.length; i++) {
		var theads = targets[i].getElementsByTagName('thead');
		var trs = theads[0].getElementsByTagName('tr');
		var ths = trs[0].getElementsByTagName('th');
		if (ths.length > 0) {
			var th = document.createElement('th');
			th.innerHTML = 'Triage';
			trs[0].appendChild(th);
			continue;
		}
	}


	// Add triage cell to rows of target tables
	for (targetN = 0; targetN < targets.length; targetN++) {
		var trs = targets[targetN].getElementsByTagName('tr');
		for (trN = 0; trN < trs.length; trN++) {
			var ths = trs[trN].getElementsByTagName('th');
			if (ths.length > 0)
				continue;
			gridflow_addTriage(trs[trN]);
		}
	}
}

function gridflow_addTriage(tr) {
	var tds = tr.getElementsByTagName('td');
	if (tds.length > 0) {
		var td = document.createElement('td');
		td.className = 'gridflow';
		var aSearch = tds[0].getElementsByTagName('a');
		if (aSearch.length) {
			var tkt = parseInt(aSearch[0].innerHTML.substr(1));
			var span1 = document.createElement('span');
			var span2 = document.createElement('span');
			var span3 = document.createElement('span');
			var select = document.createElement('select');
			select.gridflow = Object();
			select.gridflow['widget'] = span2;
			select.gridflow['actions'] = new Array();
			select.gridflow['labels'] = new Array();
			select.gridflow['widgetHTML'] = new Array();
			select.gridflow['tkt'] = tkt;
			select.gridflow['label'] = label;
			for (j = 0; j < tktDict[tkt]['labels'].length; j++) {
				var action = tktDict[tkt]['actions'][j];
				var label = tktDict[tkt]['labels'][j];
				var widget = tktDict[tkt]['widgets'][j];
				var option = document.createElement('option');
				if (widget.indexOf('&gt;') < 0) {
					// "widget" contains no HTML.
					// push its content onto label.
					option.innerHTML = label + ' ' + widget;
					select.gridflow.actions.push(action);
					select.gridflow.labels.push(label);
					select.gridflow.widgetHTML.push('');
				}
				else {
					option.innerHTML = label;
					select.gridflow.actions.push(action);
					select.gridflow.labels.push(label);
					select.gridflow.widgetHTML.push(widget);
				}
				select.appendChild(option);
			}

			select.addEventListener('change', function(ev) {
				var s = ev.target;
				s.gridflow.widget.innerHTML = s.gridflow.widgetHTML[s.selectedIndex];
				// unescape any HTML content
				s.gridflow.widget.innerHTML = s.gridflow.widget.textContent;
			}, false);


			span2.innerHTML = select.gridflow.widgetHTML[select.selectedIndex];
			// unescape any HTML content
			span2.innerHTML = span2.textContent;

			var submit = document.createElement('input');
			submit.setAttribute('type', 'submit');
			submit.setAttribute('value', 'Go');
			submit.className = 'gridflow submit';
			submit.gridflow = new Object();
			submit.gridflow['select'] = select;
			submit.gridflow['td'] = td;

			submit.addEventListener('click', function(ev) {
				var s = ev.target.gridflow.select;
				var td = ev.target.gridflow.td;
				s.gridflow.action = s.gridflow.actions[s.selectedIndex];
				s.gridflow.label = s.gridflow.labels[s.selectedIndex];

				// Prepare the ajax request data
				var ajax = {}
				ajax['id'] = s.gridflow.tkt;
				ajax['action'] = s.gridflow.action;
				ajax['extra'] = extra;
				ajax['comment'] = 'Triaged by GridFlow';

				/* See if there's a select in the widget.  If so it
				 * contains add'l information which we need to add to
				 * the request. */
				var selects = s.gridflow.widget.getElementsByTagName('select');
				if (selects.length) {
					var extra = selects[0].options[selects[0].selectedIndex].value;
					ajax[selects[0].name] = extra;
				}
				else {
					var extra = '';
				}

				// do the ajax bits, using jQuery since it's actually
				// easier even without knowing jQuery's head from its tail.
				var url = baseURL + '/gridflow/ajax'
				console.log('Executing workflow <b>' + s.gridflow.action +
				            '</b> (' + s.gridflow.label + ') on #' +
				            s.gridflow.tkt + ': <b>' + url + '</b>');
				$.ajax({
					'type': 'GET',
					'url': url,
					'data': ajax,
					'success': function (req) {
						console.log('#' + s.gridflow.tkt + ': workflow ' +
						            s.gridflow.action + ' (' +
						            extra + ') called');
						td.innerHTML = '&#x2014; ' + s.gridflow.label + ' &#x2014;';
					},
					'error': function (req) {
						console.log('#' + s.gridflow.tkt + ': workflow ' +
						            s.gridflow.action + ' (' +
						            extra + ') failed');
						console.log(req);
					},
				});
			}, false);

			span1.appendChild(select);
			span3.appendChild(submit);
			td.appendChild(span1);
			td.appendChild(span2);
			td.appendChild(span3);
			tr.appendChild(td);
		}
	}
}

$(document).ready(gridflow_init);
