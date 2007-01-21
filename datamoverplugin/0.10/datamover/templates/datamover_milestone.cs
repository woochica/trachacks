<h2>Move Milestones</h2>

<?cs if:datamover.message ?>
<div id="datamover_message" style="font-weight: bold">
<?cs var:datamover.message ?>
</div>
<?cs /if ?>

<form class="mod" method="post" action="">

<fieldset>
    <legend>Source</legend>
    <div class="field">
        <label><input type="radio" name="source" value="milestone" id="source_milestone_radio" checked="checked" />
            Milestone
        </label>
        <label><input type="radio" name="source" value="all" id="source_all_radio" />
            All
        </label>
    </div>
    <div class="field" id="source_milestone_div">
        <label>Milestone:
            <?cs each:milestone = datamover.milestones ?>
            <br/>
            <input type="checkbox" name="milestone" value="<?cs var:milestone ?>"><?cs var:milestone ?></input>
            <?cs /each ?>
        </label>
    </div>
    <div class="field" id="source_all_div" style="display: none">
        &nbsp;
    </div>
</fieldset>

<fieldset>
    <legend>Destination</legend>
    <div class="field">
        <label>Environment:
            <select name="destination">
                <?cs each:env = datamover.envs ?>
                <option value="<?cs name:env ?>"><?cs var:env.name ?></option>
                <?cs /each ?>
            </select>
        </label>
    </div>
</fieldset>

<div class="buttons">
    <input type="submit" name="copy" value="Copy" />&nbsp;
    <input type="submit" name="move" value="Move" />
</div>
    
</form>
    
    
<script type="text/javascript">
<!--
    var current_div = 'source_milestone_div';
    
    function show_div(d) {
        document.getElementById(current_div).style.display = 'none';
        document.getElementById(d).style.display = 'block';
        current_div = d;
    }
    
    function do_addEvent(d) {
        addEvent(document.getElementById(d+'_radio'), 'click', function() { show_div(d+'_div'); });
    }
    
    do_addEvent('source_milestone');
    do_addEvent('source_all');
//-->
</script>

