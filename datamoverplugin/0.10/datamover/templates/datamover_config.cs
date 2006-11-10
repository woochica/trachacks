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
        <thead><td>Name</td><td>Path</td><td>&nbsp;</td></thead>
        <tbody>
            <?cs each:env = datamover.envs ?>
            <tr>
                <td><?cs var:env.name ?></td>
                <td><?cs name:env ?></td>
                <td>Button</td>
            </tr>
            <?cs /each ?>
        </tbody>
    </table>
</form>
