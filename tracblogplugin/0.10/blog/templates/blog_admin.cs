<h2>Blog Admin<?cs if blogadmin.page == 'formats' ?> -- Formats<?cs /if ?></h2>

<?cs if blogadmin.page == 'formats' ?>
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
                        value="<?cs var:blogadmin.date_format ?>" max="50"
                        length="20" /></td>
                </tr>
            </tbody>
        </table>        
        <input type="submit" value="Change Formats" />
    </form>
    </p>
<?cs /if ?>
