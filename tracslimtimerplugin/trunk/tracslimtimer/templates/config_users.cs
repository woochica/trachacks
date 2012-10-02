    <h2>User Settings</h2>

    <table>
      <thead>
        <tr align="left">
          <th>trac user</th>
          <th>SlimTimer user</th>
          <th>CC?</th>
          <th>Report?</th>
          <th>&nbsp;</th>
          <th>&nbsp;</th>
        </tr>
      </thead>
      <tbody>
        <?cs each:item = admin.slimtimer.users ?>
        <tr>
          <td><?cs name:item ?></td>
          <td><?cs var:item.st_user ?></td>
          <td align="middle"><?cs if:item.default_cc ?>&#10004;<?cs 
          else ?>&nbsp;<?cs /if ?>
          <td align="middle"><?cs if:item.report ?>&#10004;<?cs 
          else ?>&nbsp;<?cs /if ?>
          <td><input type="button" value="Edit"
            onclick="showModForm('<?cs name:item ?>', '<?cs 
              var:item.st_user ?>', <?cs 
                if:item.default_cc ?>true<?cs else ?>false<?cs /if ?>, <?cs
                if:item.report ?>true<?cs else ?>false<?cs /if ?>)"/>
          </td>
          <td><form method="post">
            <input type="hidden" name="trac_username" 
              value="<?cs name:item ?>"/>
            <input type="hidden" name="action" value="delete"/>
            <input type="submit" value="Del"/>
          </form></td>
        </tr>
        <?cs /each ?>
      </tbody>
    </table>

    <div id="moddiv">
      <form class="mod left" id="moduser" method="post">
        <input type="hidden" name="user" value="user" id="mod_orig_username"/>
        <input type="hidden" name="action" value="modify"/>
        <fieldset>
          <legend id="mod_legend">(username)</legend>
          <div class="field left">
            <label>Trac username:<br />
              <input type="text" name="trac_username" id="mod_trac_username"
                value="" onkeyup="updateCaption()"/>
            </label>
          </div>
          <fieldset id="st_fieldset">
            <legend>SlimTimer</legend>
            <div class="field left">
              <label>Username (email):<br />
                <input type="text" name="st_username" id="mod_st_username"
                  value=""/>
              </label>
            </div>
            <div class="field">
              <label>Password:<br />
                <input type="password" name="st_password" id="mod_st_password"
                  value="" autocomplete="off"/>
              </label>
            </div>
          </fieldset>
          <br clear="all"/>
          <div class="field left">
            <label>
              <input type="checkbox" name="default_cc" id="mod_default_cc"/>
              Include in default coworkers list
            </label>
          </div>
          <div class="field">
            <label>
              <input type="checkbox" name="report" id="mod_report"/>
              Include in report
            </label>
          </div>
          <br clear="all"/>
          <input type="submit" value="Update User"/>
          <input type="button" value="Close" onclick="hideModForm()"/>
        </fieldset>
      </form>
      <br clear="all"/>
    </div>

    <form class="add" id="adduser" method="post">
      <fieldset>
        <legend>New User</legend>
        <div class="field left">
          <label>Trac username:<br />
            <input type="text" name="trac_username"/>
          </label>
          <p class="hint">e.g. tracuser</p>
        </div>
        <fieldset id="st_fieldset">
          <legend>SlimTimer</legend>
          <div class="field left">
            <label>Username (email):<br />
              <input type="text" name="st_username" />
            </label>
            <p class="hint">e.g. myname@mail.com</p>
          </div>
          <div class="field">
            <label>Password:<br />
              <input type="password" name="st_password" autocomplete="off"/>
            </label>
            <p class="hint">e.g. &lsquo;open sesame&rsquo;</p>
          </div>
        </fieldset>
        <br clear="all"/>
        <div class="field left">
          <label>
            <input type="checkbox" name="default_cc" />
            Include in default coworkers list
          </label>
        </div>
        <div class="field">
          <label>
            <input type="checkbox" name="report" />
            Include in report
          </label>
        </div>
        <input type="submit" value="Add User"/>
      </fieldset>
    </form>

