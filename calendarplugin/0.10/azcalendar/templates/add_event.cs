<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
  
<div style="margin-bottom: 10px;">
<table class="add_event" id="add_event" name="add_event">
    <form name="add" id="add" action="<?cs var:trac.href.azcalendar ?>">
    <tr >
    <td COLSPAN=2> <label for="title">Event name</label><input type="text" id="title" name="title" style="width:80%;" /> </td>
     </tr>
     <tr>
         <td><label for="time_begin">Begin(YYYY/mm/dd HH:MM)</label>
             <input type="text" id="time_begin" name="time_begin" value="<?cs var:azcalendar.time_begin ?>"/>
         </td>
        <td><label for="type">Type</label>
            <select id="type" name="type">
                <option value="0">public</option>
                <option value="1">protected</option>
                <option value="2">private</option>
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
            <option value="0">normal</option>
            <option value="1">important</option>
        </select>
        </td>
     </tr>
     <tr>
        <td> -- </td>
        <td><input type="submit" name="new_event" id="new_event" value="Save"/></td>
     </tr>
    </form>
</table>
</div>
<div id="preview" style="position:absolute;left:810px;top:150px;" >
    <?cs var:title ?></br>
    <?cs var:time_begin ?></br>
    <?cs var:time_end ?></br>
    <?cs var:type ?></br>
    <?cs var:priority ?></br>
    <?cs var:error ?></br>
    <?cs var:sql ?></br>
</div>

<?cs include "footer.cs" ?>
