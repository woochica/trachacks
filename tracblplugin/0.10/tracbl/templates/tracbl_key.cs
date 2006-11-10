<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav"></div>

<div id="content" class="blacklist">
<h1>New API key</h1>

<?cs if:tracbl.key.page == "new" ?>
<form method="post">
    <fieldset>
        <div class="field">
            <label>Email: <input type="text" name="email" /></label>
        </div>
    </fieldset>
    <div class="buttons">
        <input type="submit" name="new" value="Submit" />
    </div>
</form>
<?cs elif:tracbl.key.page == "done" ?>
<h2>Done</h2>
You API key has been emailed to you. Have a nice day.
<?cs /if ?>

<div>
<a href="<?cs var:tracbl.href.main ?>">Back</a>
</div>
</div>

<?cs include "footer.cs" ?>
