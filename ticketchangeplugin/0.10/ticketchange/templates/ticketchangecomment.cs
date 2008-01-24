<?cs include:"header.cs" ?>
<?cs include:"macros.cs" ?>
<div id="ctxtnav" class="nav"></div>
<div id="content" class="ticket">

<h1>Change Ticket Comments</h1>

<?cs if:ticketchange.message && ticketchange.redir ?>
    <b><?cs var:ticketchange.message ?></b><br />
    <a href="<?cs var:ticketchange.href ?>">Back</a>
<?cs else ?>
    <?cs with:change = ticketchange.change ?>
        <form action="<?cs var:ticketchange.href ?>" method="post">
        <hr />
           <h2>Comment at <?cs var:change.prettytime ?> by <?cs var:change.author ?></h2>
           <p><textarea id="comment" name="comment" class="wikitext" rows="10" cols="78"><?cs var:change.fields.comment.new ?></textarea></p><?cs

           if ticketchange.comment_preview ?>
               <fieldset id="preview">
                <legend>Comment Preview</legend>
                <?cs var:ticketchange.comment_preview ?>
               </fieldset><?cs
            /if ?>
           
           <div class="buttons">
               <input type="hidden" name="ticketid" value="<?cs var:ticket.id ?>" />
               <input type="hidden" name="time" value="<?cs var:ticketchange.change.time ?>" />
               <input type="hidden" name="prettytime" value="<?cs var:change.prettytime ?>" />
               <input type="hidden" name="author" value="<?cs var:change.author ?>" />
               <input type="hidden" name="href" value="<?cs var:ticketchange.href ?>" />
               <input type="hidden" name="href2" value="<?cs var:ticketchange.href2 ?>" />
               <input type="submit" name="preview" value="Preview" accesskey="r" />&nbsp;
               <input type="submit" value="Submit changes" />
           </div>
        </form>
        <script type="text/javascript" src="<?cs var:htdocs_location ?>js/wikitoolbar.js"></script>
    <?cs /with ?>
<?cs /if ?>
</div>
<?cs include "footer.cs" ?>