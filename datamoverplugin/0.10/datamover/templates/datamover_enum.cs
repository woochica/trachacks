<h2>Move Enums</h2>

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
            Enum Type
        </label>
        <label><input type="radio" name="source" value="enum" id="source_enum_radio" />
            Selected Enums
        </label>
        <label><input type="radio" name="source" value="all" id="source_all_radio" />
            All
        </label>
    </div>
    <div class="field" id="source_type_div">
        <label>Enum Type:
            <select name="enumtype">
                <?cs each:enum = datamover.enums ?>
                <option value="<?cs name:enum ?>"><?cs name:enum ?></option>
                <?cs /each ?>
            </select>
        </label>
    </div>
    <div class="field" id="source_enum_div" style="display: none">
        <label>Enums:
            <br/>
            <table>
            <?cs each:enum = datamover.enums ?>
            <tr><td valign="top" align="right"><b><?cs name:enum ?>: </b></td>
            <td>
                <?cs each:name = enum ?>
                <input type="checkbox" name="enum[<?cs name:enum ?>]" value="<?cs var:name ?>"><?cs var:name ?></input><br/>
                <?cs /each ?>
            </td></tr>
            <?cs /each ?>
            </table>
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
    do_addEvent('source_enum');
    do_addEvent('source_all');
//-->
</script>

