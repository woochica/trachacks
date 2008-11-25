var db;
var site;
var queries = [];
//alert(site);

//Dean Edwards/Matthias Miller/John Resig
	function init() {
	  // quit if this function has already been called
	  if (arguments.callee.done) return;
	
	  // flag this function so we don't do the same thing twice
	  arguments.callee.done = true;
	
	  // kill the timer
	  if (_timer) clearInterval(_timer);
	
	  savedqueries_init();
	};
	
	/* for Mozilla/Opera9 */
	if (document.addEventListener) {
	  document.addEventListener("DOMContentLoaded", init, false);
	}
	
	/* for Internet Explorer */
	/*@cc_on @*/
	/*@if (@_win32)
	  document.write("<script id=__ie_onload defer src=javascript:void(0)><\/script>");
	  var script = document.getElementById("__ie_onload");
	  script.onreadystatechange = function() {
	    if (this.readyState == "complete") {
	      init(); // call the onload handler
	    }
	  };
	/*@end @*/
	
	/* for Safari */
	if (/WebKit/i.test(navigator.userAgent)) { // sniff
	  var _timer = setInterval(function() {
	    if (/loaded|complete/.test(document.readyState)) {
	      init(); // call the onload handler
	    }
	  }, 10);
	}
	
	/* for other browsers */
	window.onload = init;
// end init code

function savedqueries_init(){
	if(!window.google || !google.gears) return;
	var navbar = document.getElementById('mainnav');
	var navlinks = navbar.getElementsByTagName('a');
	if(navlinks){
		for(var i = 0; i < navlinks.length; i++){
			if(navlinks[i].href.match(/query$/)){
				site = navlinks[i].href;
				break;
			}
		}
	}
	db = google.gears.factory.create('beta.database');
	if(db){
		db.open('trac.savedqueries');
		//db.execute('DROP TABLE Queries');
		db.execute('CREATE TABLE IF NOT EXISTS Queries' +
		' (site text, query text, name text)');
		db.execute('CREATE INDEX IF NOT EXISTS Queries_site ON Queries (site)')
		getSavedQueries();
	}
}

function createQueryItem(query){
//	GM_log("createQueryItem(" + num + ")");
	var item = document.createElement('div');
	item.setAttribute('class', 'saved_query_item');
	var link = document.createElement('a');
	link.href = site + query.query;
	link.innerHTML = query.name;
	link.setAttribute('class', 'saved_query_link');
	item.appendChild(link);
	return item;
}

function Query(rs){
	this.rowid = rs.fieldByName("rowid");
	this.query = rs.fieldByName("query");
	this.name =  rs.fieldByName("name");
}

function getSavedQueries(){
	if(!window.google || !google.gears || !db) return;
	queries = [];
	
	var rs = db.execute('SELECT rowid, site, query, name FROM Queries WHERE site=? ORDER BY Name', [site]);
	while (rs.isValidRow()) {
	  //alert(rs.field(0) + '@' + rs.field(1));
		queries.push(new Query(rs));
		rs.next();
	}
	rs.close();
}


function saveQuery(query, name){
	if(!window.google || !google.gears || !db) return;
	var rs = db.execute('INSERT INTO Queries (site, query, name) VALUES (?, ?, ?)', [site, query, name]);
	rs.close();
	var currentQuery;
	rs = db.execute('SELECT rowid, query, name FROM Queries WHERE rowid=?', [db.lastInsertRowId]);
	if(rs.isValidRow){
		currentQuery = new Query(rs);
	}
	rs.close();
	getSavedQueries();
	return currentQuery;
}

function renameQuery(query, new_name){
	query.name = new_name;
	if(!window.google || !google.gears || !db) return;
	var rs = db.execute('UPDATE Queries SET name=? WHERE rowid=?', [new_name, query.rowid]);
	rs.close();
}

function removeQuery(query){
	if(!window.google || !google.gears || !db) return;
	var rs = db.execute('DELETE FROM Queries WHERE rowid=?', [query.rowid]);
	rs.close();
	getSavedQueries();
}


function insertQueryMenu(){
	if(!window.google || !google.gears || !db) return;
	if(location.pathname.match(/query$/)){
//	GM_log("matched pathname");
		var x = document.title.indexOf(" - ");
		var title_suffix = "";
		if(x > 0){
			title_suffix = document.title.substr(x);
		}
		var currentQuery;
		for(var n = 0; n < queries.length; n++){
			var query = queries[n].query;
			if(query === location.search){
				currentQuery = queries[n];
				document.title = currentQuery.name + title_suffix;
				break;
			}
		}
		
		var content = document.getElementById('content');
		if(content){
			var heading = content.getElementsByTagName('H1')[0];
			var rename = document.createElement('a');
			rename.href="#";
			rename.setAttribute("class", "numrows");
			var remove = rename.cloneNode(true);
			var save = rename.cloneNode(true);
			rename.innerHTML = "[rename]";
			rename.addEventListener('click', function(event){
				event.stopPropagation();
				event.preventDefault();
				var new_name = window.prompt("Rename saved query:", currentQuery.name);
				if(new_name){
					renameQuery(currentQuery, new_name);
					document.title = new_name + title_suffix;
					heading.childNodes[0].nodeValue = new_name;
				}
			}, true);
			if(currentQuery){
				heading.childNodes[0].nodeValue = currentQuery.name;
				heading.appendChild(rename);
			}else{
				save.innerHTML = "[save]";
				save.addEventListener('click', function(event){
					event.stopPropagation();
					event.preventDefault();
					var new_name = window.prompt("Enter a name to save this query:", "Untitled " + queries.length);
					if(new_name){
						document.title = new_name + title_suffix;
						heading.childNodes[0].nodeValue = new_name;
						currentQuery = saveQuery(location.search, new_name)
						heading.appendChild(rename);
						heading.appendChild(remove);
						heading.removeChild(save);
					}
				}, true);
				heading.appendChild(save);
			}	
			remove.innerHTML = "[remove]";
			remove.addEventListener('click', function(event){
				event.stopPropagation();
				event.preventDefault();
				var confirm = window.confirm("Delete this saved search?");
				if(confirm){
					removeQuery(currentQuery);
					currentQuery = undefined;
					document.title = heading.childNodes[0].nodeValue = "Custom Query";
					heading.removeChild(remove);
					heading.removeChild(rename);
					heading.appendChild(save);
				}
			}, true);
			if(currentQuery){
				heading.appendChild(remove);
			}
		}
	}
	
	var content = document.getElementById('content');
	var main = document.getElementById('main');
	
	var navbar = document.getElementById('mainnav');
	var navlinks = navbar.getElementsByTagName('a');
	if(navlinks){
		for(var i = 0; i < navlinks.length; i++){
			if(navlinks[i].href.match(/query$/)){
				navlinks[i].addEventListener('click', function(event) {
					var oldMenu = document.getElementById("saved_query_menu");
					if(!oldMenu){
						if(queries.length > 0){
							//GM_log("Creating saved query menu");
							event.stopPropagation();
							event.preventDefault();
							var div = document.createElement('div');
							div.setAttribute('id', "saved_query_menu");
							div.setAttribute('style', "position: absolute; background-color:white; border: 1px solid black;padding:5px;");
							for(var n = 0; n < queries.length; n++){
								var item = createQueryItem(queries[n]);
								div.appendChild(item);
							}
							div.style.left = this.offsetLeft + "px";
							div.style.top = this.offsetTop + this.offsetHeight + "px";
							this.offsetParent.insertBefore(div, this.nextSibling);
							var hideDiv = function(e) {
								div.parentNode.removeChild(div);
								document.removeEventListener('click', hideDiv, false);
							};
							document.addEventListener('click', hideDiv, false);
						}
					}
				}, true);
			}
		}
	}
}
addEvent(window, 'load', insertQueryMenu);
