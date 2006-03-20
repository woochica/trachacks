<h2>General Settings</h2>

<form class="mod" id="modhackinstallgeneral" method="post">
    <fieldset>
        <legend>Setting</legend>
        <div class="field">
            <label>URL:<br />
                <input type="text" name="url" value="<?cs var:hackinstall.url ?>" />
            </label>
        </div>
        <div class="field">
            <label>Version<br />
                <input type="text" name="version" id="version_field" value="<?cs var:hackinstall.version ?>" <?cs if:hackinstall.override_version ?>disabled="true"<?cs /if ?>/><br />
                Override autodetect: <input type="checkbox" name="override_version" id="override_version" <?cs if:!hackinstall.override_version ?>checked="true"<?cs /if ?>/>
            </label>
        </div>
    </fieldset>
    <div class="buttons">
        <input type="submit" value="Apply changes">
        <input type="submit" name="update" value="Update metadata" />
    </div>
</form>

<script type="text/javascript">
<--
    var override_version = document.getElementById("override_version");
    var change_override = function() {
        document.getElementById("version_field").disabled = ! override_version.checked;
    }
    
    addEvent(override_version, "change", change_override);
//--!>
</script>

