    <h2>Basic Settings</h2>

    <form class="mod" id="modbasic" method="post">
      <div class="field">
        <label>SlimTimer API key:<br />
          <input type="text" name="api_key" 
            value="<?cs var:admin.slimtimer.api_key ?>"/>
        </label>
        <p class="hint">e.g. 94d641ad952e7e0...<br/>
        This can be the API key for any user, not necessarily one of the users
        listed in the Users page.
        </p>
        <p class="hint"><a href="http://www.slimtimer.com/help/api">Get your
        API key</a></p>
      </div>
      <div class="buttons">
        <input type="submit" value="Apply changes"/>
      </div>
    </form>

