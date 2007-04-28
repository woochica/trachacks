function add_ctxtnav(html) {
    var ctxtnav_bar = $('#ctxtnav');
    ctxtnav_bar.find('li:last-child').removeClass('last').after('<li class="last">'+html+'</li>');
}
