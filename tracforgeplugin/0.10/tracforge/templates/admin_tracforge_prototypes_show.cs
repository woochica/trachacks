<?cs if:tracforge.prototypes.action == "new" ?>
<h2>New Prototype</h2>
<?cs else ?>
<h2>Editing <?cs var:tracforge.prototypes.name ?></h2>
<?cs /if ?>

<a href="<?cs var:tracforge.href.prototypes ?>">Back</a>

<?cs def:step(name, args, text, show) ?>
<div id="step_<?cs var:name ?>" class="step" <?cs if:!show ?>style="display: none"<?cs /if ?>>
    <div class="step-buttons">
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/x.gif" alt="Remove" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/down.gif" alt="Down" />
        <img src="<?cs var:tracforge.href.htdocs ?>/img/greyscale/up.gif" alt="Up" />
    </div>
    <div class="step-name"><?cs var:name ?></div>
    <div class="step-args"><label>Arguments:<input type="text" name="args" value="<?cs var:args ?>" /></label></div>
    <hr /><div class="step-text"><?cs var:text ?></div>
 </div>
 <?cs /def ?>


<div id="steps">
<?cs each:step = tracforge.prototypes.initialsteps ?>
    <?cs call:step(step.action, step.args, tracforge.prototypes.steps[step.action].description, 1) ?>
<?cs /each ?>
<?cs call:step("TEMPLATE", "", "", 0) ?>
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
<form id="form" method="post">
<div>
    <div id="buttons">
        <?cs if:tracforge.prototypes.action != "new" ?>
            <input type="submit" name="delete" value="Delete" />
        <?cs /if ?>
        <input type="submit" name="cancel" value="Cancel" />
        <input type="submit" name="save" value="Save" />
    </div>
    <?cs if:tracforge.prototypes.action == "new" ?>
    <label>Name: 
        <input type="text" name="name" />
    </label>
    <?cs /if ?>
    <input type="hidden" name="data" />
</div>
</form>
</div>


<script type="text/javascript">

var DURATION = 400;

function remove_step() {
    $(this).unbind("click"); // So double clicks don't cause problems.
    var step = $(this).parents(".step");
    step.animate({height:'hide',opacity:'hide'}, 400, function() {
        $(this).remove()
    });
    var step_type = step.id().substr(5);
    $("#addstep-form select[@name=type]").find("option[@value="+step_type+"]").remove().end()
                                         .append('<option value="'+step_type+'">'+step_type+'</option>');
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
        var step = Array();
        step[0] = this.id.substr(5);
        step[1] = $(this).find("input[@name=args]").val()
        steps.push(step);
    });
    steps.pop(); // This is the template div
    steps.pop(); // This will always be the addstep div
    steps.pop(); // Form and buttons
    return steps;
}

$(function() {
    $("#form").submit(function() {
        var buf = Array();
        var steps = collect_steps();
        for(i in steps) {
            buf.push(steps[i][0]+","+steps[i][1]);
        }
        // NOTE: The 'data' literal is just so there is a difference between a JS failure and an empty prototype
        $(this).find("input[@name=data]").val('data'+buf.join("|"));
    });
            

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
});
</script>
