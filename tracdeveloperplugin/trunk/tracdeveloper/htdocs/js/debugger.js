jQuery.fn.initTree = function(url, callback) {
  var params = {token: $("#token").val()};
  return this.each(function() {
    $("a.toggle", this).each(function() {
      $(this).click(function() {
        $(this).toggleClass("expanded");
        var detail = $(this).parents("dt:first").next();
        if ($(this).is(".expanded")) {
          detail.show();
        } else {
          detail.hide();
        }
        if (!detail.children().length) {
          $.get(url + "/" + $(this).parents("dt:first").get(0).id, params, function(response) {
            detail.html(response).initTree(url, callback);
            if (callback) callback(detail);
          });
        }
        return false;
      });
      $(this).parents("dt:first").next().hide();
    });
  });
}
