<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="report">

<h2>XML-RPC exported functions</h2>

<table class="listing tickets">
<thead>
<tr>
<th>Function</th>
<th>Description</th>
<th>Permission required</th>
</tr>
</thead>

<?cs set idx = #0 ?>
<tbody>
<?cs each:function = xmlrpc.functions ?>
<tr class="color3-<?cs if idx % #2 == 0 ?>even<?cs else ?>odd<?cs /if ?>" style="">
<td><?cs var:function.0?></td><td><?cs var:function.1?></td><td><?cs var:function.2 ?></td>
</tr>
<?cs set idx = idx + #1 ?>
<?cs /each ?>
</tbody>
</table>

</div>

<?cs include:"footer.cs"?>
