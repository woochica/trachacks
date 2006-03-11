<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="report">

<h2>XML-RPC exported functions</h2>

<dl>
<?cs each:namespace = xmlrpc.functions ?>

<dt><h3><?cs var:namespace.namespace ?> - <?cs var:namespace.description ?></h3></dt>
<dd>
<table class="listing tickets">
<thead>
<tr>
<th>Function</th>
<th>Description</th>
<th><nobr>Permission required</nobr></th>
</tr>
</thead>

<?cs set idx = #0 ?>
<tbody>
<?cs each:function = namespace.methods ?>
<tr class="color3-<?cs if idx % #2 == 0 ?>even<?cs else ?>odd<?cs /if ?>" style="">
<td><nobr><?cs var:function.0?></nobr></td><td><?cs var:function.1?></td><td><?cs var:function.2 ?></td>
</tr>
<?cs set idx = idx + #1 ?>
<?cs /each ?>
</tbody>
</table>
</dd>
<?cs /each ?>
</dl>

</div>

<?cs include:"footer.cs"?>
