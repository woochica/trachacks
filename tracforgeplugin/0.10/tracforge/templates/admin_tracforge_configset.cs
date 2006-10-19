<h2>TracForge Config Sets</h2>

<form class="addnew" method="post">
    <fieldset>
        <legend>Add Entry</legend>
        <div class="field">
            <label>Tag: <input type="text" name="tag" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Section: <input type="text" name="section" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Key: <input type="text" name="key" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Value: <input type="text" name="value" class="textwidget" /></label>
        </div>
        <div class="field"
            <table>
                <tr>
                    <td>Action: </td>
                    <td><label><input type="radio" name="action" value="add" checked="checked" />Add</label></td>
                </tr>
                <tr>
                    <td>&nbsp;</td>
                    <td><label><input type="radio" name="action" value="del" />Delete</label></td>
                </tr>
            </table>
        </div>
        <p class="help">Add a new configuration entry</p>
        <div class="buttons">
            <input type="submit" name="add" value="Add" />
        </div>
    </fieldset>
</form>

<form method="post">
<table class="listing">
<thead>
<tr>
    <th class="sel">&nbsp;</th>
    <th>Section</th>
    <th>Key</th>
    <th>Value</th>
    <th>Action</th>
</tr>
</thead>
<?cs each:tag = tracforge.tags ?>
    <tr class="header">
        <th colspan="0"><?cs name:tag ?></th>
    </tr>
    <?cs each:config = tag ?>
    <tr>
        <td><input type="checkbox" name="rows" value="<?cs name:tag ?>/<?cs var:config.section ?>/<?cs var:config.key ?>" /></td>
        <td><?cs var:config.section ?></td>
        <td><?cs var:config.key ?></td>
        <td><?cs var:config.value ?></td>
        <td><?cs var:config.action ?></td>
    </tr>
    <?cs /each ?>
<?cs /each ?>
</table>
</form>
