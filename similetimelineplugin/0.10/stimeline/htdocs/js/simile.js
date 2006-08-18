var tl;
var es;

function doLoad() {
  var eventSource = new Timeline.DefaultEventSource();
  es = eventSource;
  var bandInfos = [
    Timeline.createBandInfo({
        showEventText:  false,
        trackHeight:    0.5,
        trackGap:       0.2,
        eventSource:    eventSource,
        date:           "Jul 28 2006 00:00:00 GMT",
        width:          "20%", 
        intervalUnit:   Timeline.DateTime.WEEK, 
        intervalPixels: 100
    }),
    Timeline.createBandInfo({
        eventSource:    eventSource,
        date:           "Jul 28 2006 00:00:00 GMT",
        width:          "80%", 
        intervalUnit:   Timeline.DateTime.DAY, 
        intervalPixels: 100
    })
  ];
  bandInfos[0].syncWith = 1;
  bandInfos[0].highlight = true;
  tl = Timeline.create(document.getElementById("trac-timeline"), bandInfos, 0);
}

var resizeTimerID = null;
function doResize() {
    if (resizeTimerID == null) {
        resizeTimerID = window.setTimeout(function() {
            resizeTimerID = null;
            tl.layout();
        }, 500);
    }
}


// Dean Edwards/Matthias Miller/John Resig

function init() {
    // quit if this function has already been called
    if (arguments.callee.done) return;

    // flag this function so we don't do the same thing twice
    arguments.callee.done = true;

    // kill the timer
    if (_timer) clearInterval(_timer);

    // do stuff
    doLoad();
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



window.onresize = doResize;
