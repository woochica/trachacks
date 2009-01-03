<?cs include "header.cs"?>
<?cs include "macros.cs"?>
<!--

 Copyright (c) 2007-2008 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
 Author: Francois Granade - fg at nexb dot com
 Licensed under the same license as Trac - http://trac.edgewall.org/wiki/TracLicense

-->

<div id="ctxtnav" class="nav">
    <h2>Ticket import</h2>
    <ul>Importing tickets</ul>
</div>
    

<div id="content" class="report">
<h1>Import a file</h1>

<p>
This module lets you import tickets in batch, from an Excel spreadsheet or comma-separated-values (CSV) file.
</p>
<p>
The file or worksheet to import should contain:
<ul>
<li>In the first line, the names of the fields to import.</li>
<li>In the remaining of the file or worksheet, the data to import.</li>
</ul>
</p>
<p>
The fields must be Trac fields. The valid fields for this Trac instance are:
<?cs set numfields = #0 ?>
<?cs each field = fields.items ?>
<?cs set numfields = numfields + #1 ?>
<b><?cs var: field ?></b><?cs if fields.count == $numfields + #1 ?> and <?cs elif fields.count != $numfields ?>, <?cs /if ?><?cs /each ?>. Field names are case-insensitive: 'summary', 'Summary', 'SUMMARY' refer to the same field. The order of the fields does not matter. If you want to import columns that are not Trac fields yet, these fields must have been created as custom fields in Trac (It is easy to create new fields, but must be done by the Trac administrator in the Trac configuration file. Note that it is better for usability to limit the numbers of custom fields).
</p>
<p>The only required fields are either:
<ul>
<li> <b>summary</b>. If tickets are found in Trac with the same 'summary'<?cs if:reconciliate_by_owner_also ?>, and the same owner if present<?cs /if ?>, they will be reconciliated: no ticket will be added, but modified or added values for other fields, will be imported (of course, any replaced value is always kept in the Change History for the ticket). As a consequence, <b>you cannot have two tickets (or two rows in your spreadsheet) with the same summary <?cs if:reconciliate_by_owner_also ?> and owner<?cs /if ?></b>. If the summary <?cs if:reconciliate_by_owner_also ?>and owner don't<?cs else ?>doesn't<?cs /if ?> match any existing ticket, a new ticket will be created.</li>
</ul>
or:
<ul>
<li> <b>ticket</b>. This field should contain ticket numbers: if tickets are found with the same number, they will be reconciliated. If it is empty for some rows, they will be imported as new tickets. This can be used to export (using a report and save as CSV), modify in Excel, and re-import tickets.</li>
</ul>
</p>
<p>
First, you will be shown a preview of the changes, and then you will be able to execute the import. The first step (uploading and previewing) will not modify the database.
</p>
<p>
Components, Milestones, etc... found in the spreadsheet will be added to Trac if they do not exist yet. You may want to customize them after that in the Admin section.
</p>

<form id="importer" method="post" enctype="multipart/form-data" action="">
   <div class="field">
     <label for="import-file">File to import:</label>
       <input type="file" name="import-file" />
   </div>
   <br/>
   <div class="field">
     <label for="sheet">If Excel spreadsheet, index of the worksheet to import:</label>
       <select name="sheet">
       <option value="1">1</option>
       <option value="2">2</option>
       <option value="3">3</option>
       <option value="4">4</option>
       <option value="5">5</option>
       <option value="6">6</option>
       <option value="7">7</option>
       <option value="8">8</option>
       <option value="9">9</option>
       </select>
       <i>Note: worksheets containing non-data (e.g., charts) are skipped when counting the worksheets.</i>
   </div>
  <div class="buttons">
   <input type="hidden" name="action" value="upload" />
   <input type="submit" value="Upload file and preview import" />
   <input type="submit" name="cancel" value="Cancel" />
  </div>
 </form>
</div>

<?cs include:"footer.cs"?>
