<h2>Delete Ticket<?cs if:ticketdelete.page=='comments' ?> Changes<?cs /if ?></h2>

<?cs if:ticketdelete.message ?>
    <b><?cs var:ticketdelete.message ?></b><br />
    <a href="<?cs var:ticketdelete.href ?>">Back</a>
<?cs elif:ticketdelete.page == 'delete' ?>
    <p>
        <b>Note: This is intended only for use in very odd circumstances.<br />
        It is usually a better idea to resolve a ticket as invalid, than to remove it from the database.</b>
    </p>

    <form method="post" onsubmit="return confirm('Are you sure you want to do this?')">
        Ticket ID: <input type="text" name="ticketid" /><br />
        Again: <input type="text" name="ticketid2" /><br />
        <input type="submit" value="Delete" />
    </form>
<?cs elif:ticketdelete.page == 'comments' ?>
    <?cs if:len(ticketdelete.changes) ?>
        <p>Please selet a change to delete</p>
        <?cs each:change = ticketdelete.changes ?>
            <div>
                <b><?cs var:change.prettytime ?></b><br />
                Change by <?cs var:change.author ?><br />
                <?cs each:field = change.fields ?>
                    <?cs if:name(field)=='comment' ?>
                        Comment: <?cs var:field.new ?><br />
                    <?cs else ?>
                        <?cs name:field ?>: From '<?cs var:field.old ?>' to '<?cs var:field.new ?>'<br />
                    <?cs /if ?>
                <?cs /each ?>
                <form method="post">
                    <input type="hidden" name="ts" value="<?cs name:change ?>" />
                    <input type="submit" name="delete_all" value="Delete Entire Change" />
                    <input type="submit" name="delete_only" value="Delete Comment Only" />
                </form>
            </div><br />
        <?cs /each ?>
        <br />
        <a href="<?cs var:ticketdelete.href ?>">Back</a>
    <?cs else ?>
        <form method="post">
            <p>Select a ticket ID to change.</p>
            <p>
                Ticket ID: <input type="text" name="ticketid" /><br />
                <input type="submit" value="Submit" />
            </p>
        </form>
    <?cs /if ?>
<?cs /if ?>
