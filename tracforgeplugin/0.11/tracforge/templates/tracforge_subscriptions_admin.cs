<h2>Manage Subscriptions</h2>

<form class="addnew" id="addenum" method="post">
    <fieldset>
        <legend>Add Subscription</legend>
        <div class="field">
            <label>Environment:<input type="text" name="env" /></label>
        </div>
        <div class="field">
            <label>Type:<select name="type"><?cs each:type = tracforge.types ?><option value="<?cs var:type ?>"><?cs var:type ?></option><?cs /each ?></select></label>
        </div>
        <div class="buttons">
            <input type="submit" name="add" value="Add" />
        </div>
    </fieldset>
</form>

<?cs each:type = tracforge.subscriptions ?>
<h3><?cs name:type ?></h3>
<ul>
<?cs each:sub = type ?>
<li><?cs var:sub ?></li>
<?cs /each ?>
</ul>
<?cs /each ?>

