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
        <th colspan="5"><?cs var:tag ?></th>
    </tr>
    <?cs each:section = tracforge.configs[tag] ?><?cs each:key = section ?>
    <tr>
        <td><input type="checkbox" name="rows" value="<?cs var:tag ?>/<?cs name:section ?>/<?cs name:key ?>" /></td>
        <td><?cs name:section ?></td>
        <td><?cs name:key ?></td>
        <td><?cs var:key.0 ?></td>
        <td><?cs var:key.1 ?></td>
    </tr>
    <?cs /each ?><?cs /each ?>
<?cs /each ?>
</table>
<div class="buttons">
    <input type="submit" name="delete" value="Delete selected" />
</div>
</form>
