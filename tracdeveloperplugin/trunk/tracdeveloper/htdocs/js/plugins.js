$(document).ready(function () {
  $("#content.plugins li div.info").hide();
  $("#content.plugins li h3 a").click(function() {
    var item = $(this).parents("li:first");
    var info = item.find("div.info");
    var showing = info.is(":visible");
    $("div.listing li").removeClass("highlighted").removeClass("expanded").find("div.info").hide();
    if (!showing) {
      item.toggleClass("expanded");
      info.toggle().find("a.xref").each(function() {
        $(this.getAttribute("href")).parents("li:first").addClass("highlighted");
      });
    }
    this.blur();
    return false;
  });
  $("#content.plugins li div.info a.xref").click(function() {
    $(this.getAttribute("href")).parents("li:first").find("h3 a").click();
  });
});
