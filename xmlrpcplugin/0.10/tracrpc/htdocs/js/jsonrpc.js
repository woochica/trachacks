jQuery.jsonrpc = function(url) {
  this.url = url;
  this.server = {};
  this.callbacks = Array();
  this.id = 0;
};

// Register a new server-side RPC method
jQuery.jsonrpc.prototype.expose = function(name) {
  var path = name.split('.');
  var current = this.server;
  var jsonrpc = this;

  for (var i = 0; i < path.length - 1; ++i) {
    if (!current[path[i]]) {
      current[path[i]] = {}
    }
    current = current[path[i]];
  }

  var inject = function(callback) {
    var arglist = Array.prototype.slice.apply(arguments).slice(1);

    var data = {
      method: name,
      params: $.toJSON(arglist),
    }

    var ajax_options = {
      url: jsonrpc.url,
      dataType: 'json',
      success: function(result) {
        return callback(result['result']);
      },
      data: data,
    };

    for (var key in inject) {
      if (key != 'prototype') {
        ajax_options[key] = inject[key];
      }
    }

    $.ajax(ajax_options);
  };

  current[path[path.length - 1]] = inject;

  return inject
};
