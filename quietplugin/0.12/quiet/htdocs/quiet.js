var refresh = function(a,o){
    a.text(o.label);
    if (o.is_quiet)
      jQuery('body').addClass('quiet');
    else
      jQuery('body').removeClass('quiet');
}

var listen = function(listeners){
    for (var i=0; i!=listeners.length; i++){
        bind_and_ask(listeners[i]);
    }
}

var bind_and_ask = function(listener){
    var el = jQuery(listener.selector);
    el.click(function(e){
        // first check if no need for action
        if ((listener.action == 'enter' && !jQuery('body').hasClass('quiet')) ||
            (listener.action == 'leave' && jQuery('body').hasClass('quiet'))) {
            
            // check for conditional
            if (listener.only){
                var only = jQuery(listener.only);
                var eq = new RegExp(listener.eq);
                if (eq) {
                    if (!only.val().match(eq))
                        return; // expected regex does not match
                } else if (!only.length)
                    return; // only does not exist
            }
            
            // passed conditional (if any), so prompt
            var answer = confirm("Do you want to " + listener.action + " quiet mode?");
            if (answer) {
                query(listener.action);
                if (listener.submit){
                    e.preventDefault();
                    return false;
                }
                return true;
            }
        }
    });
}
