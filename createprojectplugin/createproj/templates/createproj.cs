<h2>Create New Project</h2>
    <?cs if:len(createproject.errormsg) ?>
        <div id="content" class="error">
            <p class="message">
                <h2><?cs var:createproject.errortitle ?></h2>
                <p><?cs var:createproject.errormsg ?></p>
            </p>
        <div>
    <?cs /if ?>
    <form class="createprojectform" method="post"> <!-- action="<?cs var:trac.href.guestbook ?>"> -->
        <div class="field">
          <label>
            Name:<br />
            <input type="text" name="createproject.full_name" size="30" value="<?cs var:createproject.full_name ?>"/>
          </label>
        </div>
        <div class="field">
          <label>
            Description:<br />
            <textarea class="textfield" name="createproject.desc" rows="20"><?cs var:createproject.desc ?></textarea>
          </label>
        </div>
        <div class="field">
          <label>
            Directory name:<br />
            <input class="textfield" type="text" name="createproject.dir_name" size="30" value="<?cs var:createproject.dir_name ?>"/>
          </label>
        </div>
        <div class="field">
          <label>
            InterTrac prefix:<br />
            <input class="textfield" type="text" name="createproject.intertrac_name" size="12" value="<?cs var:createproject.intertrac_name ?>"/>
          </label>
        </div>
        <div class="field">
          <label>
            Repository type:<br />
            <input class="textfield, arbitrarywidth" type="text" name="createproject.repos_type" value="<?cs var:createproject.repos_type ?>"/>
          </label>
        </div>
        <div class="field">
          <label>
            Repository path:<br />
            <input class="textfield, arbitrarywidth" type="text" name="createproject.repos_path" value="<?cs var:createproject.repos_path ?>"/>
          </label>
        </div>
<!--
        <div class="field">
          <label>
            :<br />
            <input class="textfield" type="text" name="" value=""/>
          </label>
        </div>
-->
        <input type="hidden" name="action" value="newproject"/>
        <div class="buttons">
          <input type="submit" name="submit" value="Submit"/>
        </div>
    </form>
</form>
