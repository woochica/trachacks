<h2>Delete Ticket<?cs if:ticketdelete.page=='comments' ?> Changes<?cs /if ?></h2>

<?cs if:ticketdelete.message && ticketdelete.redir ?>
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
        <?cs if:ticketdelete.message ?><p><b><?cs var:ticketdelete.message ?></b></p><?cs /if ?>
        <p>Please selet a change to delete</p>
        
        <p><form method="post"><table class="listing">
            <thead><tr><th class="sel">&nbsp;</th><th>Field</th><th>Old Value</th><th>New Value</th><th>&nbsp;</th></tr></thead>
            <tbody>
                <?cs each:change = ticketdelete.changes ?>
                    <tr>
                        <td><input type="checkbox" name="dontcare" value="dontcare" id="checkbox_<?cs name:change ?>" /></td>
                        <td colspan="3"><b>Change at <?cs var:change.prettytime ?> by <?cs var:change.author ?></b></td>
                        <td><input type="submit" name="delete_<?cs name:change ?>" value="Delete change" /></td>
                    <tr>
                    <?cs each:field = change.fields ?>
                    <tr>
                        <td><input type="checkbox" id="checkbox<?cs name:field ?>_<?cs name:change ?>" name="delete" value="<?cs name:field ?>_<?cs name:change ?>" /></td>
                        <td><?cs name:field ?></td>
                        <?cs if:name(field) == 'comment' ?>
                            <td colspan="2"><?cs var:field.new ?></td>
                        <?cs else ?>
                            <td><?cs var:field.old ?></td>
                            <td><?cs var:field.new ?></td>
                        <?cs /if ?>
                        <td><input type="submit" name="delete<?cs name:field ?>_<?cs name:change ?>" value="Delete field" /></td>
                    </tr>
                    <?cs /each ?>
                <?cs /each ?>
            </tbody>
        </table><br /><input type="submit" name="multidelete" value="Delete Checked" /></form></p>
        
        <script type="text/javascript">
        <!--
            function toggleboxen(me, boxen) 
            {
                status = document.getElementById("checkbox_" + me).checked;
                boxen.pop() // Remove the last (blank) entry.
                for (box in boxen) {
                    //alert("Changing checkbox"+boxen[box]+"_"+me);
                    document.getElementById("checkbox"+boxen[box]+"_"+me).checked = status;
                }
            }
            
            <?cs each:change = ticketdelete.changes ?>
            addEvent(document.getElementById("checkbox_<?cs name:change ?>"), "change", function() {
                var boxen = Array(<?cs each:field = change.fields ?>"<?cs name:field ?>",<?cs /each ?>"");
                toggleboxen("<?cs name:change ?>", boxen); //Array(<?cs each:field = change.fields ?>"<?cs name:field ?>",<?cs /each ?>));
            });
            <?cs each:field = change.fields ?>
            addEvent(document.getElementById("checkbox<?cs name:field ?>_<?cs name:change ?>"),"change", function() {
                if(!document.getElementById("checkbox<?cs name:field ?>_<?cs name:change ?>").checked) {
                    document.getElementById("checkbox_<?cs name:change ?>").checked = 0;
                }
            });
            <?cs /each ?>
            <?cs /each ?>


        //-->
        </script>


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
