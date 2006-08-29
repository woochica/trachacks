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
            <label>Environment: <input type="text" name="env" class="textwidget" /></label>
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
            <tr><th class="sel">&nbsp;</th><th>Short Name</th><th>Full Name</th></tr>
        </thead>
        <tbody>
            
        </tbody>
    </table>
    <div class="buttons">
        <input type="submit" name="delete" value="Delete selected projects" />
    </div>
</form>
