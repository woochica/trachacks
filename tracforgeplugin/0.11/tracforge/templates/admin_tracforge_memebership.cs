<h2>TracForge Project Membership</h2>

<form id="addrole" class="addnew" method="post">
    <fieldset>
        <legend>Add New Role</legend>
        <div class="field">
            <label>Project: <select name="project">
                <?cs each:proj = tracforge.projects?>
                <option value="<?cs name:proj ?>"><?cs name:proj ?></option>
                <?cs /each ?>
            </select></label>
        </div>
        <div class="field">
            <label>User: <input type="text" name="user" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Role: <select name="role">
                <option value="member">Member</option>
                <option value="admin">Admin</option>
            </select></label>
        </div>
        <p class="help">Add a new user role</p>
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
    <th>User</th>
    <th>Role</th>
</tr>
</thead>
<?cs each:proj = tracforge.projects ?>
    <tr class="header">
        <th colspan="0"><?cs name:proj ?></th>
    </tr>
    <?cs each:mem = proj.members ?>
        <tr>
            <td>&nbsp;</td>
            <td><?cs name:mem ?></td>
            <td><?cs var:mem ?></td>
        </tr>
    <?cs /each ?>
<?cs /each ?>

</table>
</form>
