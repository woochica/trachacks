<h2>Datamover Configuration</h2>

<?cs if:datamover.any_mutable ?>
<form class="addnew" id="addenv" method="post">
    <fieldset>
        <legend>Add Environment</legend>
        <div class="field">
            <label>Path: <input type="text" name="env_path" /></label>
        </div>
        <div class="buttons">
            <input type="submit" name="add" value="Add" />
        </div>
    </fieldset>
</form>
<?cs /if ?>

<form class="mod" id="modconfig" method="post">
    <table class="listing">
        <thead><th class="sel">&nbsp;</th><th>Name</th><th>Path</th></thead>
        <tbody>
            <?cs each:env = datamover.envs ?>
            <tr>
                <td><input type="checkbox" name="sel" value="<?cs name:env ?>" <?cs if:!env.mutable ?>disabled="disabled"<?cs /if ?> /></td>
                <td><?cs var:env.name ?></td>
                <td><?cs name:env ?></td>
            </tr>
            <?cs /each ?>
        </tbody>
    </table>
    <div class="buttons">
        <input type="submit" name="remove" value="Remove selected items" />
    </div>
    <p class="help">
        You can only delete environments from mutable sources. All others are disabled.
    </p>
</form>
