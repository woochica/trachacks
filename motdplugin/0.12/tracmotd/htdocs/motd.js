
// 
// motd scripts
//


function showMotd() {

    addMotdDiv();

    var motd = document.getElementById("motdframe");

    motd.style.top = "200px";
    motd.style.left = "200px";
    //motd.style.width = "500px";
    //motd.style.height = "400px";

    var h = getHeader();
    var m = getMessages();
    motd.innerHTML = h;
    motd.innerHTML += "<div id=\"motdcontent\">" + m +"</div>";
    motd.innerHTML += "<div id=\"motdfooter\"><button onclick=\"hideMotd();\">Close Message(s)</button></div>";

    //var sbar = document.getElementById("motdfooter");
    //sbar.style.marginTop = (parseInt(400)-40) + "px";
    motd.style.visibility = "visible";
}

function hideMotd() {
    var motd = document.getElementById("motdframe");
    motd.style.visibility = "hidden";
    for (m in TracMotd) {
        msgObj = TracMotd[m];
        valid_until = msgObj['valid_until'];
	setCookie(m, "shown", valid_until);
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

function setCookie(name, value, valid_until) {
    expires = new Date(getDateFromFormat(valid_until, "yyyy-MM-dd HH:mm")).toGMTString();
    document.cookie = name + "=" + value + "; expires=" + expires + "; path=/";
}

function getHeader() {
    var header = "";
    header += "<table id=\"motdheader\"><tr><td>Systemmessage available</td></tr></table>";
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



// add our showMotd to "onload"
//
addEvent(window, 'load', showMotd);

