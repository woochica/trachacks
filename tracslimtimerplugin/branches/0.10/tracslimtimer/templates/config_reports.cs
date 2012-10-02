    <h2>Reporting Settings</h2>

    <form class="mod" id="modbasic" method="post">
      <fieldset>
        <legend>Database</legend>
        <div class="field">
          <label>Host:<br />
            <input type="text" name="db_host" 
              value="<?cs var:admin.slimtimer.host ?>"/>
          </label>
        </div>
        <div class="field left">
          <label>Username:<br />
            <input type="text" name="db_username" 
              value="<?cs var:admin.slimtimer.username ?>"/>
          </label>
          <p class="hint">e.g. tt_recorder</p>
        </div>
        <div class="field">
          <label>Password:<br />
            <input type="password" name="db_password" 
              value="<?cs var:admin.slimtimer.password ?>"
              autocomplete="off"/>
          </label>
          <p class="hint">e.g. &lsquo;open sesame&rsquo;</p>
        </div>
        <br clear="all"/>
        <div class="field">
          <label>Database:<br />
            <input type="text" name="db_dsn" 
              value="<?cs var:admin.slimtimer.database ?>"/>
          </label>
          <p class="hint">e.g. timetracking</p>
        </div>
      </fieldset>
      <fieldset>
        <legend>Logging</legend>
        <div class="field">
          <label>Log file:<br />
            <input type="text" name="report_log" size="50"
              value="<?cs var:admin.slimtimer.report_log ?>"/>
          </label>
          <p class="hint">e.g. 
            <?cs var:admin.slimtimer.default_report_log ?></p>
        </div>
      </fieldset>
      <div class="buttons">
        <input type="submit" name="apply" value="Apply changes"/>
      </div>
    </form>

    <form class="mod" id="report" method="post">
      <fieldset>
        <legend>On-demand report</legend>
        <div class="field">
          <label>Days:<br />
            <input type="text" name="days"
              value="14"/>
          </label>
        </div>
        <div class="buttons">
          <input type="submit" name="dump" value="Dump report">
        </div>
      </fieldset>
    </form>

