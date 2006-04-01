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
                        value="<?cs var:blogadmin.date_format ?>"
                        length="60" /></td>
                </tr>
                <tr>
                    <td>Page Name Format String</td>
                    <td><input type="text" name="page_format" 
                        value="<?cs var:blogadmin.page_format ?>"
                        length="60" /></td>
                </tr>
            </tbody>
        </table>        
        <input type="submit" value="Change Formats" />
    </form>
    </p>
<?cs /if ?>
