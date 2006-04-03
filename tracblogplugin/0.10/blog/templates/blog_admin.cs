<h2>Blog Admin<?cs if blogadmin.page == 'defaults' ?> -- Defaults<?cs /if ?></h2>

<?cs if blogadmin.page == 'defaults' ?>
    <form class="mod" id="modbasic" method="post">
        <fieldset>
            <legend>Defaults</legend>
            <div class="field">
                <label>Date Format String:<br />
                    <input type="text" name="date_format" 
                    value="<?cs var:blogadmin.date_format ?>" />
                </label>
            </div>
            <div class="field">
                <label>Page Name Format String:<br />
                    <input type="text" name="page_format" 
                    value="<?cs var:blogadmin.page_format ?>" />
                </label>
            </div>
            <div class="field">
                <label>Default Tag (<a href="<?cs var:base_url ?>/tags"
                    >view all tags</a>):<br/>
                    <input type="text" name="default_tag" 
                    value="<?cs var:blogadmin.default_tag ?>" />
                </label>
            </div>
        </fieldset>
        <div class="buttons">
            <input type="submit" value="Apply Changes" />
        </div>
    </form>
<?cs /if ?>
<?cs if ! 1 ?>
<?cs if blogadmin.page == 'defaults' ?>
    <p>
    <form method="post">
        <table class="listing">
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Date Format String</td>
                    <td><input type="text" name="date_format" 
                        value="<?cs var:blogadmin.date_format ?>"
                        length="60" /></td>
                </tr>
                <tr>
                    <td>Page Name Format String</td>
                    <td><input type="text" name="page_format" 
                        value="<?cs var:blogadmin.page_format ?>"
                        length="60" width="100%" /></td>
                </tr>
                <tr>
                    <td>Default Tag (<a href="<?cs var:base_url ?>/tags"
                        >view all tags</a>)</td>
                    <td><input type="text" name="default_tag" 
                        value="<?cs var:blogadmin.default_tag ?>"
                        length="60" width="100%" /></td>
                </tr>
            </tbody>
        </table>        
        <input type="submit" value="Set Defaults" />
    </form>
    </p>
<?cs /if ?>
<?cs /if ?>
