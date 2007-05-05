<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div style="margin-bottom: 10px;">
<table class="add_event" id="update_event" name="update_event">
    <form name="add" id="add" action="<?cs var:trac.href.azcalendar ?>">
    <tr >
        <td COLSPAN=2> <label for="title">Event name</label>
        <input type="text" id="title" name="title" value="<?cs var:azcalendar.title ?>" style="width:80%;" /> 
     </td>
     </tr>
     <tr>
         <td><label for="time_begin">Begin(YYYY/mm/dd HH:MM)</label>
             <input type="text" id="time_begin" name="time_begin" value="<?cs var:azcalendar.time_begin ?>"/>
         </td>
        <td><label for="type">Type</label>
            <select id="type" name="type">
            <option value="0" <?cs if:azcalendar.event.public ?> selected="selected"<?cs /if ?> >public</option>
                <option value="1" <?cs if:azcalendar.event.protected ?> selected="selected"<?cs /if ?> >protected</option>
                <option value="2" <?cs if:azcalendar.event.private ?> selected="selected"<?cs /if ?> >private</option>
            </select>
        </td>
     </tr>
     <tr>
        <td>
            <label for="time_end">End(YYYY/mm/dd HH:MM)</label>
            <input type="text" id="time_end" name="time_end" value="<?cs var:azcalendar.time_end ?>"/>
        </td>
        <td>
        <label for="priority">Event priority</label>
        <select id="priority" name="priority">
            <option value="0" <?cs if:azcalendar.priority.normal ?> selected="selected"<?cs /if ?> >normal</option>
            <option value="1"<?cs if:azcalendar.priority.important ?> selected="selected"<?cs /if ?> >important</option>
        </select>
        </td>
     </tr>
     <tr>
     <td>  </td>
        <td>
            <input type="submit" name="update_event" id="update_event" value="Save"/>
            <input type="submit" name="delete_event" id="delete_event" value="Delete"/>
        </td>
     </tr>
     <input type="hidden" name="evid" id="evid" value="<?cs var:azcalendar.evid ?>" />
    </form>
</table>
<div class="comments">
<h2>Comments:</h2>
<ul>
       <li>Last update: <?cs var:azcalendar.last_update ?> by <?cs var:azcalendar.author ?></li>
</ul>
</div>
<?cs include "footer.cs" ?>
