<h2>TracForge Admin</h2>

<form id="addproject" class="addnew" method="post">
    <fieldset>
        <legend>Add New Project</legend>
        <div class="field">
            <label>Short Name: <input type="text" name="shortname" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Full Name: <input type="text" name="fullname" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Environment: <input type="text" name="env_path" class="textwidget" /></label>
        </div>
        <div class="field">
            <label>Prototype: <select name="prototype">
                <?cs each:p = tracforge.prototypes ?>
                    <option value="<?cs var:p ?>"><?cs var:p ?></option>
                <?cs /each ?>
            </select></label>
        </div>
        <p class="help">Create a new project</p>
        <div class="buttons">
            <input type="submit" name="create" value="Create" />
        </div>        
    </fieldset>
</form>

<form method="post">
    <table class="listing" id="projectlist">
        <thead>
            <tr><th class="sel">&nbsp;</th><th>Short Name</th><th>Full Name</th><th>Env Path</th></tr>
        </thead>
        <tbody>
            <?cs each:proj = tracforge.projects ?>
            <tr>
                <td>&nbsp</td><td><?cs name:proj ?></td>
                <td><?cs var:proj.fullname ?></td>
                <td><?cs var:proj.env_path ?></td>
            </tr>
            <?cs /each ?>
        </tbody>
    </table>
    <div class="buttons">
        <input type="submit" name="delete" value="Delete selected projects" />
    </div>
</form>
