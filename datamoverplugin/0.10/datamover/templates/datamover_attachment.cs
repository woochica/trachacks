<h2>Move Attachments</h2>

<?cs if:datamover.message ?>
<div id="datamover_message" style="font-weight: bold">
<?cs var:datamover.message ?>
</div>
<?cs /if ?>

<form class="mod" method="post" action="">

<fieldset>
    <legend>Source</legend>
    <div class="field">
        <label><input type="radio" name="source" value="type" id="source_type_radio" checked="checked" />
            Type
        </label>
        <label><input type="radio" name="source" value="wiki" id="source_wiki_radio" />
            Wiki Page
        </label>
        <label><input type="radio" name="source" value="ticket" id="source_ticket_radio" />
            Ticket
        </label>
        <label><input type="radio" name="source" value="all" id="source_all_radio" />
            All
        </label>
    </div>
    <div class="field" id="source_type_div">
        <label>Type:
            <select name="type">
                <option value="wiki">Wiki</option>
                <option value="ticket">Ticket</option>
            </select>
        </label>
    </div>
    <div class="field" id="source_wiki_div" style="display: none">
        <label>Wiki Page (only showing pages with attachments):
            <br/>
            <?cs each:page = datamover.wiki_pages ?>
            <br/>
            <input type="checkbox" name="wiki" value="<?cs var:page ?>"><?cs var:page ?></input>
            <?cs /each ?>
        </label>
    </div>
    <div class="field" id="source_ticket_div" style="display: none">
        <label>Ticket ID:
            <input type="text" name="ticket" />
        </label>
    </div>
    <div class="field" id="source_all_div" style="display: none">
        <p style="font-style: italic">Note: this will take a while</p>
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
    var current_div = 'source_type_div';
    
    function show_div(d) {
        document.getElementById(current_div).style.display = 'none';
        document.getElementById(d).style.display = 'block';
        current_div = d;
    }
    
    function do_addEvent(d) {
        addEvent(document.getElementById(d+'_radio'), 'click', function() { show_div(d+'_div'); });
    }
    
    do_addEvent('source_type');
    do_addEvent('source_wiki');
    do_addEvent('source_ticket');
    do_addEvent('source_all');
//-->
</script>

