<h2>New Prototype</h2>

<a href="<?cs var:tracforge.href.prototypes ?>">Back</a>

<?cs def:teststep(name, text) ?>
<div id="step_<?cs var:name ?>" class="step">
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/x.gif" alt="Remove" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/down.gif" alt="Down" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/up.gif" alt="Up" />
    </div>
    <?cs var:text ?>
</div>
<?cs /def ?>

<div id="steps">
<?cs call:teststep("one", "Foo") ?>
<?cs call:teststep("two", "Bar") ?>
<?cs call:teststep("three", "Baz") ?>
<?cs call:teststep("four", "Blah") ?>
<div id="addstep" class="step">
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/plus.gif" alt="Add" />
    </div>
    <form id="addstep-form">
        <select name="type">
            <?cs each:step = tracforge.prototypes.steps ?>
            <option value="<?cs var:step ?>"><?cs var:step ?></option>
            <?cs /each ?>
        </select>
    </form>
</div>
</div>

<script type="text/javascript">
function remove_step() {
    var step = $(this).parents(".step");
    step.animate({height:'hide',opacity:'hide'}, 400, function() {
        $(this).remove()
    });
    var step_type = step.id().substr(5);
    $("#addstep-form select[@name=type]").append('<option value="'+step_type+'">'+step_type+'</option>');
}
    
function up_step() {
    var me = $(this).parents(".step");
    var prev = $(me).prev(".step");
    if(prev.length == 0) { return; } // Top item
    prev.animatedSwap(me, 400);
}
    
function down_step() {
    var me = $(this).parents(".step");
    var next = $(me).next(".step");
    if(next.length == 0) { return; } // Bottom item
    if(next.id() == "addstep") { return; }
    me.animatedSwap(next, 400);
}

var STEP_HTML = Array(
'<div id="step_((name))" class="step" style="display: none">',
'   <div class="step-buttons">',
'       <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/x.gif" alt="Remove" />',
'       <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/down.gif" alt="Down" />',
'       <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/up.gif" alt="Up" />',
'   </div>',
'   ((name))',
'</div>'
);

function step_html(name) {
    return (STEP_HTML.join("\n")+"\n").replace(/\(\(name\)\)/g, name);
}

$(function() {
    $("img[@alt=Remove]").click(remove_step);
    $("img[@alt=Up]").click(up_step);
    $("img[@alt=Down]").click(down_step);
        
    $("#addstep img[@alt=Add]").click(function() {
        var step_type = $("#addstep-form select[@name=type]").val();
        $(this).parents(".step").before(step_html(step_type));
        $(this).parents(".step").prev()
            .animate({height: 'show'}, 400)
            .find("img[@alt=Remove]").click(remove_step).end()
            .find("img[@alt=Up]").click(up_step).end()
            .find("img[@alt=Down]").click(down_step);
        $("#addstep-form option[@value="+step_type+"]").remove();
    });
});
</script>
