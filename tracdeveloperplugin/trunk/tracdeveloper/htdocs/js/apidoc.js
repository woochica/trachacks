jQuery.fn.showDocs = function(uri) {
  return this.each(function() {
    var offset = (function(elem) {
      var offset = {left: 0, top: 0};
      do {
        offset.left += elem.offsetLeft || 0;
        offset.top += elem.offsetTop || 0;
        elem = elem.offsetParent;
      } while (elem);
      return offset;
    })(this);

    $("#apidoc").fadeOut("fast");
    var div = $("<div id='apidoc'></div>");
    function hideDocs() {
      div.fadeOut("fast", function() { div.remove(); });
      $(document).unbind("keypress");
    }
    div.load(uri, {}, function(response, status, xhr) {
      if (status == "error") return;
      $("<button>Close</button>").click(hideDocs).prependTo(div.find(".title"));
      div.css({top: offset.top + "px", left: offset.left + "px"});
      div.appendTo("body");
      $(document).bind("keypress", function(e) {
        if (e.keyCode == 27) { // escape
          hideDocs();
        }
      });
    });
  });
}
