<h2>New Prototype</h2>

<a href="<?cs var:tracforge.href.prototypes ?>">Back</a>

<?cs def:step(name, text, show) ?>
<div id="step_<?cs var:name ?>" class="step" <?cs if:!show ?>style="display: none"<?cs /if ?>>
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/x.gif" alt="Remove" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/down.gif" alt="Down" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/up.gif" alt="Up" />
    </div>
    <div class="step-name"><?cs var:name ?></div>
    <div class="step-args"><label>Arguments:<input type="text" name="args" /></label></div>
    <hr /><div class="step-text"><?cs var:text ?></div>
 </div>
 <?cs /def ?>


<div id="steps">
<?cs each:step = tracforge.prototypes.initialsteps ?>
    <?cs call:step(step, tracforge.prototypes.steps[step].description, 1) ?>
<?cs /each ?>
<?cs call:step("TEMPLATE", "", 0) ?>
<div id="addstep" class="step">
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/plus.gif" alt="Add" />
    </div>
    <form id="addstep-form">
        <select name="type">
            <?cs each:step = tracforge.prototypes.liststeps ?>
            <option value="<?cs var:step ?>"><?cs var:step ?></option>
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
    var select = $("#addstep-form select[@name=type]");
    if($(select).find("option[@value="+step_type+"]").length == 0) {
        select.append('<option value="'+step_type+'">'+step_type+'</option>');
    }
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
    if(next.id() == "addstep" || next.id() == "step_TEMPLATE") { return; }
    me.animatedSwap(next, 400);
}

var DESCRIPTIONS = {
<?cs each:step = tracforge.prototypes.steps ?>
    <?cs name:step ?>: "<?cs var:step.description ?>",
<?cs /each ?>
};

function collect_steps() {
    var steps = Array();
    $("#steps").children().each(function() {
        steps.push(this.id.substr(5));
    });
    steps.pop(); // This is the template div
    steps.pop(); // This will always be the addstep div
    return steps;
}

$(function() {
    $("img[@alt=Remove]").click(remove_step);
    $("img[@alt=Up]").click(up_step);
    $("img[@alt=Down]").click(down_step);
    
    $("#addstep img[@alt=Add]").click(function() {
        var step_type = $("#addstep-form select[@name=type]").val();
        if(step_type == "") { return; }

        $("#step_TEMPLATE").clone().insertBefore("#step_TEMPLATE")
            .id("step_"+step_type)
            .find(".step-name").empty().prepend(step_type).end()
            .find(".step-text").empty().prepend(DESCRIPTIONS[step_type]).end()
            .animate({height: 'show'}, DURATION)
            .find("img[@alt=Remove]").click(remove_step).end()
            .find("img[@alt=Up]").click(up_step).end()
            .find("img[@alt=Down]").click(down_step);
        $("#addstep-form option[@value="+step_type+"]").remove();
    });
    
    $("#collect").click(function() {
        alert(collect_steps().join("\n"));
    });
});
</script>
