jQuery.fn.initTree = function(url, callback) {
  var params = {token: $("#token").val()};
  return this.each(function() {
    $("a.toggle", this).each(function() {
      $(this).click(function() {
        $(this).toggleClass("expanded");
        var detail = $(this).parents("dt:first").next().toggle();
        if (detail.children().length == 0) {
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
