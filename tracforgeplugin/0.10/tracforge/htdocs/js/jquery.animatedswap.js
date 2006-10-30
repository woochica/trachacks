jQuery.fn.animatedSwap = function(next, duration) {
    var me = this;
    // Find positions and sizes
    var my_pos = jQuery.extend(
        jQuery.iUtil.getPosition(me.get(0)),
        jQuery.iUtil.getSize(me.get(0))
    );
    var next_pos = jQuery.extend(
        jQuery.iUtil.getPosition(next.get(0)),
        jQuery.iUtil.getSize(next.get(0))
    );
        
    var me_copy = $(me).clone().css('display', 'block')
                               .css('position', 'absolute') 
                               .css('width', my_pos.w + "px")
                               .css("height", my_pos.h + "px")
                               .css("left", my_pos.x + "px")
                               .css("top", my_pos.y - (my_pos.wb-my_pos.w) + 8 + "px")
                               //.css("background-color", "pink")
                               .appendTo('body');

    var next_copy = $(next).clone().css('display', 'block')
                                   .css('position', 'absolute') 
                                   .css('width', next_pos.w + "px")
                                   .css("height", next_pos.h + "px")
                                   .css("left", next_pos.x + "px")
                                   .css("top", next_pos.y - (next_pos.wb-next_pos.w) + 8 + "px")
                                   //.css("background-color", "pink")
                                   .appendTo('body');
                                       
            
    me.css('visibility', 'hidden');
    next.css('visibility', 'hidden');
            
    me_copy.animate({top:(1.0*next_copy.top().replace("px",""))}, duration);
    next_copy.animate({top:(1.0*me_copy.top().replace("px",""))}, duration, function() {
        me.css('visibility', 'visible');
        next.css('visibility', 'visible');
        next.after(me);
        me_copy.hide().remove();
        next_copy.fadeOut(1, function() {
           this.parentNode.removeChild(this);
        });
    });
};

