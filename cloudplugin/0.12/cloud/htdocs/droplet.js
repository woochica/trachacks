/*
 * messages
 */
var warning = function(msg){
  var html = '<div id="warning" class="system-message">'+msg+'</div>';
  html = html.replace(/&lt;/g,'<').replace(/&gt;/g,'>');
  jQuery('#ctxtnav').after(html);
}
