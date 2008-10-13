<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="cn" xml:lang="cn" charset="utf-8">
<head><title>Available Milestones</title></head>
<body>

<h2>MMV: Admin milestones</h2>


<form id="mmv_admin" action="mmv_admin" method="post">

  <div class="field">

  <table class="listing" id="millist">
   <thead>
    <tr>
        <th class="sel">Enable</th>
        <th>Milestone</th>
        <th>Start Date</th>
        <th>End Date</th>
    </tr>
   </thead><tbody><?cs
   each:milestone = milestones ?>
   <tr>
    <td><input type="checkbox" name="sel" value="<?cs var:milestone.name ?>" <?cs 
     if:milestone.enabled ?> checked="checked"<?cs
     /if ?> /></td>
    <td>
     <a href="<?cs var:milestone.href ?>"><?cs var:milestone.name ?></a>
     <input type="text" name="milestone" 
     value="<?cs var:milestone.name ?>" style="display:none;" />
    </td>
    <td>
     <input type="text" id="startdate_<?cs var:milestone.name ?>" name="startdate" 
       value="<?cs var:milestone.startdate ?>" title="<?cs var:date_hint ?>" />
    </td>
    <td>
     <input type="text" id="enddate_<?cs var:milestone.name ?>" name="enddate"
       value="<?cs var:milestone.enddate ?>" title="<?cs var:date_hint ?>" />
    </td>

   </tr><?cs
   /each ?></tbody>
  </table>
    
    <input type="submit" name="save" value="Save" accesskey="s" />  
    <input type="submit" name="repair" value="Repair" accesskey="r" />  
  </div>
  
</form>

</html>
