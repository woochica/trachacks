<h2>Move Tickets</h2>

<?cs if:datamover.message ?>
<div id="datamover_message" style="font-weight: bold">
<?cs var:datamover.message ?>
</div>
<?cs /if ?>

<form class="mod" method="post" action="">

<fieldset>
    <legend>Source</legend>
    <div class="field">
        <label><input type="radio" name="source" value="component" id="bycomponent_radio" checked="checked" />
            Component
        </label>&nbsp;
        <label><input type="radio" name="source" value="ticket" id="byticket_radio" />
            Ticket
        </label>
    </div>
    <div class="field" id="bycomponent_div">
        <label>Component:
            <select name="component">
                <?cs each:comp = datamover.components ?>
                <option value="<?cs var:comp ?>"><?cs var:comp ?></option>
                <?cs /each ?>
            </select>
        </label>
    </div>
    <div class="field" id="byticket_div" style="display: none">
        <label>Ticket ID:
            <input type="text" name="ticket" />
        </label>
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
    var current_div = 'bycomponent_div';
    
    function show_div(d) {
        document.getElementById(current_div).style.display = 'none';
        document.getElementById(d).style.display = 'block';
        current_div = d;
    }
    
    function do_addEvent(d) {
        addEvent(document.getElementById(d+'_radio'), 'change', function() { show_div(d+'_div'); });
    }
    
    do_addEvent('bycomponent');
    do_addEvent('byticket');
//-->
</script>

