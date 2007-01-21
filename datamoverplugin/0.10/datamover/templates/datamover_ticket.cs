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
        <label><input type="radio" name="source" value="component" id="source_component_radio" checked="checked" />
            Component
        </label>
        <label><input type="radio" name="source" value="ticket" id="source_ticket_radio" />
            Ticket
        </label>
        <label><input type="radio" name="source" value="all" id="source_all_radio" />
            All
        </label>
        <label><input type="radio" name="source" value="query" id="source_query_radio" />
            Query
        </label>
    </div>
    <div class="field" id="source_component_div">
        <label>Component:
            <select name="component">
                <?cs each:comp = datamover.components ?>
                <option value="<?cs var:comp ?>"><?cs var:comp ?></option>
                <?cs /each ?>
            </select>
        </label>
    </div>
    <div class="field" id="source_ticket_div" style="display: none">
        <label>Ticket ID:
            <input type="text" name="ticket" />
        </label>
    </div>
    <div class="field" id="source_all_div" style="display: none">
        &nbsp;
    </div>
    <div class="field" id="source_query_div" style="display: none">
        <label>Query String:
            <input type="text" name="query" />
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
    var current_div = 'source_component_div';
    
    function show_div(d) {
        document.getElementById(current_div).style.display = 'none';
        document.getElementById(d).style.display = 'block';
        current_div = d;
    }
    
    function do_addEvent(d) {
        addEvent(document.getElementById(d+'_radio'), 'click', function() { show_div(d+'_div'); });
    }
    
    do_addEvent('source_component');
    do_addEvent('source_ticket');
    do_addEvent('source_all');
    do_addEvent('source_query');    
//-->
</script>

