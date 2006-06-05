<?cs include:"header.cs" ?>
<?cs include:"macros.cs" ?>

<div id="content">
<form action="" method="post">
    <fieldset>
        <legend>Rename Page</legend>
        <div class="field">
            <label>Original name:<br />
                <input type="text" name="src_page" value="<?cs var:wikirename.src ?>" />
            </label>
        </div>
        <div class="field">
            <label>New name:<br />
                <input type="text" name="dest_page" value="" />
            </label>
        </div>
    </fieldset>
    <div class="buttons">
        <input type="submit" name="submit" value="Apply" />
    </div>
</form> 
</div>

<?cs include:"footer.cs" ?>
