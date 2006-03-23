<h2>General Settings</h2>

<?cs def:help_link(text) ?><a href="javascript:alert('<?cs var:text ?>')"><font size="-3"><i>(?)</i></font></a><?cs /def ?>

<form class="mod" id="modhackinstallgeneral" method="post">
    <fieldset>
        <legend>Setting</legend>
        <div class="field">
            <label>URL: <?cs call:help_link("This is the URL to the Trac-Hacks server, you should not need to change it.") ?><br />
                <input type="text" name="url" value="<?cs var:hackinstall.url ?>" /> 
            </label>
        </div>
        <div class="field">
            <label>Version: <?cs call:help_link("This is version used when installing plugins. You should only need to change it if HackInstall detects your version incorrectly") ?><br />
                <input type="text" name="version" id="version_field" value="<?cs var:hackinstall.version ?>" <?cs if:!hackinstall.override_version ?>disabled="true"<?cs /if ?>/><br />
                Override autodetect: <input type="checkbox" name="override_version" id="override_version" <?cs if:hackinstall.override_version ?>checked="true"<?cs /if ?>/>
            </label>
        </div>
        <div class="buttons">
            <input type="submit" name="update_metadata" value="Check for updates" />
            <input type="submit" name="save_settings" value="Apply changes">
        </div>
    </fieldset>
    <fieldset>
        <legend>Pending Updates</legend>
        <?cs if:len(hackinstall.updates)>0 ?>
            <fieldset>
                <legend>Plugins</legend>
                <?cs each:plugin = hackinstall.updates.plugins ?>
                    <p>
                        <b><?cs name:plugin ?></b><br />
                        Upgrade from revision <?cs var:plugin.installed ?> to revision <?cs var:plugin.current ?> 
                        <a href="http://trac-hacks.org/log/<?cs var:plugin.lowername ?>?rev=<?cs var:plugin.current ?>&stop_rev=<?cs var:plugin.installed+1 ?>&verbose=on">(View changes)</a>
                        <input type="checkbox" name="doupdate_<?cs name:plugin ?>" />
                    </p>
                <?cs /each ?>
            </fieldset>
            <div class="buttons">
                <input type="submit" name="update_all" value="Update All" />
                <input type="submit" name="update_selected" value="Update Selected" />
            </div>
        <?cs else ?>
            No pending updates
        <?cs /if ?>
    </fieldset>
</form>

<script type="text/javascript">
<!--
    var override_version = document.getElementById("override_version");
    var change_override = function() {
        document.getElementById("version_field").disabled = ! override_version.checked;
    };
    
    addEvent(override_version, "change", change_override);
//-->
</script>

