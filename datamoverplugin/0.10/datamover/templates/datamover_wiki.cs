<h2>Move Wiki Pages</h2>

<?cs if:datamover.message ?>
<div id="datamover_message" style="font-weight: bold">
<?cs var:datamover.message ?>
</div>
<?cs /if ?>

<form class="mod" method="post" action="">

<fieldset>
    <legend>Source</legend>
    <div class="field">
        <label><input type="radio" name="source" value="prefix" id="source_prefix_radio" checked="checked" />
            Prefix
        </label>
        <label><input type="radio" name="source" value="glob" id="source_glob_radio" />
            Glob
        </label>
        <label><input type="radio" name="source" value="regex" id="source_regex_radio" />
            Regex
        </label>
    </div>
    <div class="field" id="source_prefix_div">
        <label>Prefix:
            <input type="text" name="prefix" />
        </label>
    </div>
    <div class="field" id="source_glob_div" style="display: none">
        <label>Glob:
            <input type="text" name="glob" />
        </label>
    </div>
    <div class="field" id="source_regex_div" style="display: none">
        <label>Regular Expression:
            <input type="text" name="regex" />
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
    var current_div = 'source_prefix_div';
    
    function show_div(d) {
        document.getElementById(current_div).style.display = 'none';
        document.getElementById(d).style.display = 'block';
        current_div = d;
    }
    
    function do_addEvent(d) {
        addEvent(document.getElementById(d+'_radio'), 'change', function() { show_div(d+'_div'); });
    }
    
    do_addEvent('source_prefix');
    do_addEvent('source_glob');
    do_addEvent('source_regex');
//-->
</script>

