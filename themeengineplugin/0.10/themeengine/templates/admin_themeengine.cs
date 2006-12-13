<h2>Theme Chooser</h2>

<style type="text/css">

/**
 * This <div> element is wrapped by statically around the list
 * inside the HTML document.
 */
.jcarousel-scope {
    position: relative;
    width: 640px;
    -moz-border-radius: 10px;
    background: #EEF7D4;
    /*background: #FFFECC;*/
    padding: 20px 35px;
}

/**
 * Similar styles will be applied by jCarousel. But we additionally
 * add it here for better displaying with browsers having
 * javascript disabled.
 */
.jcarousel-list {
    overflow: hidden;
    margin: 0;
    padding: 0;
}

.jcarousel-list li {
    float: left;
    list-style: none;
}

/**
 * The button-elements are added statically in the HTML document
 * to illustrate how to cutomize the prev/next controls.
 *
 * We set display:none to hide them from browsers having
 * javascript. jCarousel will show them automatically.
 */
.jcarousel-next {
    display: none;
    position: absolute;
    top: 205px;
    right: 5px;
    cursor: pointer;
}

.jcarousel-next-disabled {
    cursor: default;
    opacity: .5;
    -moz-opacity: .5;
    filter: alpha(opacity=50);
}

.jcarousel-prev {
    display: none;
    position: absolute;
    top: 205px;
    left: 5px;
    cursor: pointer;
}

.jcarousel-prev-disabled {
    cursor: default;
    opacity: .5;
    -moz-opacity: .5;
    filter: alpha(opacity=50);
}

</style>

<div id="carousel">
 <img src="<?cs var:themeengine.href.htdocs ?>/img/prev.gif" border="0" class="jcarousel-prev" />
 <img src="<?cs var:themeengine.href.htdocs ?>/img/next.gif" border="0" class="jcarousel-next" />
 <ul>
  <?cs each:theme = themeengine.info ?>
  <li><img height="400" width="640" src="<?cs var:themeengine.href.screenshot ?>/<?cs name:theme ?>" id="<?cs name:theme ?>" /></li>
  <?cs /each ?>
 </ul>
 <div id="theme_name" style="text-align: center; font-weight: bold; font-size: 1.4em"><?cs var:themeengine.current ?></div>
 <div id="theme_desc" style="text-align: center"></div>
 <div style="text-align: center">
  <form method="post">
   <input type="hidden" name="theme" id="form_theme_name" />
   <input type="submit" value="Use this theme" />
  </form>
 </div>
</div>


<script type="text/javascript">

var descriptions = {};
<?cs each:theme = themeengine.info
?>descriptions['<?cs name:theme ?>'] = '<?cs var:theme.description ?>';
<?cs /each ?>

function change_handler(car, elm, ind, state) {
    var theme = $(elm).find('img').id();
    $('#theme_name').html(theme);
    $('#form_theme_name').val(theme);
    $('#theme_desc').html(descriptions[theme]);
}

$(function() {
    $('#carousel').jcarousel({
        itemStart: <?cs var:themeengine.current_index ?>,
        itemVisible: 1,
        itemScroll: 1,
        itemVisibleInHandler: change_handler
    });
});
</script>
