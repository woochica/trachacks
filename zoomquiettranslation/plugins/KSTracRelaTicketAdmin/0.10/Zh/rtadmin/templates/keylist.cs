<?cs include "header.cs"?>

<div id="ctxtnav" class="nav"></div>


<div id="content" class="keylist">
	<h1>Keylist</h1>

	<table class="listing" id="milelist">
		<thead>
		<tr><th>里程碑</th>
		</tr>
		</thead>

		<tbody><?cs
		each:item = data ?>
			<tr>
			<td><a href="<?cs var:item.filename ?>" title="<?cs var:item.m_full ?>"><?cs var:item.m_full ?></a></td>
			</tr><?cs
		/each ?>
		</tbody>
	</table>

</div>

<?cs include "footer.cs"?>



