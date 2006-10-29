<h2>New Prototype</h2>

<a href="<?cs var:tracforge.href.prototypes ?>">Back</a>

<?cs def:teststep(num, name, text) ?>
<div id="step_<?cs var:name ?>" class="step">
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/x.gif" alt="Remove" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/down.gif" alt="Down" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/up.gif" alt="Up" />
    </div>
    <?cs var:text ?>
</div>
<?cs /def ?>

<?cs call:teststep(1, "one", "Foo") ?>
<?cs call:teststep(2, "two", "Bar") ?>
<?cs call:teststep(3, "three", "Baz") ?>
<?cs call:teststep(4, "four", "Blah") ?>

<script type="text/javascript">
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
                                   .css("top", my_pos.y - (my_pos.wb-my_pos.w) + "px")
                                   //.css("background-color", "pink")
                                   .appendTo('body');

        var next_copy = $(next).clone().css('display', 'block')
                                       .css('position', 'absolute') 
                                       .css('width', next_pos.w + "px")
                                       .css("height", next_pos.h + "px")
                                       .css("left", next_pos.x +"px")
                                       .css("top", next_pos.y - (next_pos.wb-next_pos.w) + "px")
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

    $(function() {
        $("img[@alt=Remove]").click(function() { 
            $(this).parents(".step").animate({height:'hide',opacity:'hide'}, 400, function() {
                $(this).remove()
            });
        });

        $("img[@alt=Up]").click(function() {
            var me = $(this).parents(".step");
            var prev = $(me).prev(".step");
            if(prev.length == 0) { return; } // Top item
            prev.animatedSwap(me, 400);
        });

        $("img[@alt=Down]").click(function() {
            var me = $(this).parents(".step");
            var next = $(me).next(".step");
            if(next.length == 0) { return; } // Bottom item
            me.animatedSwap(next, 400);            
        });
    });
</script>
