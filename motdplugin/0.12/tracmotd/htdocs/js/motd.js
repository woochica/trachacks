// 
// motd scripts
//


function showMotd() {

    addMotdDiv();

    var motd = document.getElementById("motdframe");

    motd.style.top = "200px";
    motd.style.left = "200px";
    motd.style.width = TracMotdFrame['frame_width'] + "px";    // "500px";
    motd.style.height = TracMotdFrame['frame_height'] + "px";  //"400px";

    var h = getHeader();
    var m = getMessages();

    motd.innerHTML = h;
    motd.innerHTML += "<div id=\"motdcontent\">" + m +"</div>";
    motd.innerHTML += "<table id=\"motdfooter\"><tr><td><button onclick=\"hideMotd();\">Acknowledge Message(s)</button></td></tr></table>";

    var cont = document.getElementById("motdcontent");
    cont.style.height = (TracMotdFrame['frame_height'] - 66) + "px";

    motd.style.visibility = "visible";
}

function hideMotd() {
    var motd = document.getElementById("motdframe");
    motd.style.visibility = "hidden";
    for (m in TracMotd) {
        msgObj = TracMotd[m];
        valid_until = msgObj['valid_until'];
	if (msgObj['repeat'] == "no") {
	    setCookie(m, "shown", valid_until);
	} else {
	    // check whether to repeat again
	    var oldCookie = readCookie(m);
	    if (oldCookie == '') {
	        var toRepeat = msgObj['repeat'].split("-");
		if (toRepeat.length != 2) {
		    // syntax-error in repeat, so ignore it...
		    setCookie(m, "shown", valid_until);
		} else {
		    var now = new Date().getTime();
		    var cVal = "R-" + (toRepeat[0]-1) + "-" + toRepeat[1] + "-" + now;
		    setCookie(m, cVal, valid_until);
		}
	    } else {
	        // message already shown, check whether to show again
		var cArr = oldCookie.split("-");
		if ((cArr.length != 4) || (cArr[0] != "R")) {
		    // wrong cookie, ignore it and don't show message again
		    setCookie(m, "shown", valid_until);
		} else {
		    //
		    if ((cArr[1] - 1) > 0) {
		        var now = new Date().getTime();
		        var cVal = "R-" + (cArr[1]-1) + "-" + cArr[2] + "-" + now;
			setCookie(m, cVal, valid_until);
		    } else {
		        // ready, don't show message any longer
			setCookie(m, "shown", valid_until);
		    }
		}
	    }
	}
    }
}


// helper functions
//
function addEvent(obj, evType, fn) {
    if (obj.addEventListener) {
        obj.addEventListener(evType, fn, false);
	return true;
    } else if (obj.attachEvent) {
        var r = obj.attachEvent("on"+evType, fn);
	return r;
    } else {
        return false;
    }
}

// add <div> for motd to body
//
function addMotdDiv() {
    var mMotd = document.createElement("div");
    mMotd.id = "motdframe";
    mMotd.className = "motdframe";
    window.document.body.appendChild(mMotd);
}

function getHeader() {
    var header = "";
    header += "<table id=\"motdheader\"><tr><td>Message from SysAdmin</td></tr></table>";
    return header;
}

function getMessages() {
    var motd = '';
    for (m in TracMotd) {
	msgObj = TracMotd[m];
	title = msgObj['title'];
	//priority = msgObj['priority'];
        message = msgObj['message'];
	motd = motd + "<h4><b>" + title + "</b></h4>";
	motd = motd + "<p>" + message + "</p>";
    }
    return motd;
}

function setCookie(name, value, valid_until) {
    var expires = new Date(getDateFromFormat(valid_until, "yyyy-MM-dd HH:mm")).toGMTString();
    document.cookie = name + "=" + escape(value) + ";expires=" + expires + ";path=/";
}

function readCookie(cookieName) {
    var re = new RegExp('[; ]'+cookieName+'=([^\\s;]*)');
    var sMatch = (' '+document.cookie).match(re);
    if (cookieName && sMatch) return unescape(sMatch[1]);
    return '';
}




// add our showMotd to "onload"
//
addEvent(window, 'load', showMotd);

