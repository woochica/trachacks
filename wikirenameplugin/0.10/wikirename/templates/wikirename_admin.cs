<h2>Wiki Rename</h2>

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
                <input type="text" name="dest_page" value="<?cs var:wikirename.dest ?>" />
            </label>
        </div>
    </fieldset>
    <div class="buttons">
        <input type="hidden" name="redirect" value="<?cs var:wikirename.redir ?>" />
        <input type="submit" name="submit" value="Apply" />
    </div>
</form> 

