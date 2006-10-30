<h2>New Prototype</h2>

<a href="<?cs var:tracforge.href.prototypes ?>">Back</a>

<div id="steps">
<div id="addstep" class="step">
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/plus.gif" alt="Add" />
    </div>
    <form id="addstep-form">
        <select name="type">
            <?cs each:step = tracforge.prototypes.steps ?>
            <option value="<?cs name:step ?>"><?cs name:step ?></option>
            <?cs /each ?>
        </select>
    </form>
</div>
</div>

<a href="#" id="collect">Collect</a>

<script type="text/javascript">

var DURATION = 400;

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
'   <div class="step-name">((name))</div>',
'   <div class="step-args"><label>Arguments:<input type="text" name="args" /></label></div>',
'   <hr /><div class="step-text">((text))</div>',
'</div>'
);

var DESCRIPTIONS = {
<?cs each:step = tracforge.prototypes.steps ?>
    <?cs name:step ?>: "<?cs var:step.description ?>",
<?cs /each ?>
};

function step_html(name) {
    return (STEP_HTML.join("\n")+"\n").replace(/\(\(name\)\)/g, name).replace(/\(\(text\)\)/g, DESCRIPTIONS[name]);
}

function collect_steps() {
    var steps = Array();
    $("#steps").children().each(function() {
        steps.push(this.id.substr(5));
    });
    steps.pop(); // This will always be the addstep div
    return steps;
}

$(function() {
    $("#addstep img[@alt=Add]").click(function() {
        var step_type = $("#addstep-form select[@name=type]").val();
        if(step_type == "") { return; }
        $(this).parents(".step").before(step_html(step_type));
        $(this).parents(".step").prev()
            .animate({height: 'show'}, DURATION)
            .find("img[@alt=Remove]").click(remove_step).end()
            .find("img[@alt=Up]").click(up_step).end()
            .find("img[@alt=Down]").click(down_step);
        $("#addstep-form option[@value="+step_type+"]").remove();
    });
    
    $("#collect").click(function() {
        alert(collect_steps());
    });
    
    // Start the list off with this entry
    $("#addstep-form select[@name=type]").val("MakeTracEnvironment");
    var temp = DURATION;
    DURATION = 1;
    $("#addstep img[@alt=Add]").click();
    DURATION = temp;
});
</script>
