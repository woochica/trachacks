<?cs set:global_reports_js = 1 ?>
<?cs include "myHeader.cs" ?>
<?cs include "macros.cs" ?>

<div id="content">
	<h1>STractistics</h1>
	<form id="prefs" method="post">
		<div>
			<label>View activity from <input type="text" size="8" name="end_date" value="<?cs var:timeframe.end_date ?>" /></label> and
		 	<label><input type="text" size="3" name="weeks_back" value="<?cs var:timeframe.weeks_back ?>" /> weeks back</label>.
	 	</div>
	 	<div class="buttons">
	  		<input type="submit" name="update" value="Update" />
	 	</div>
	</form>	
	<div class="report-wrapper">
		<h2>Repository activity: <em>Most active repository authors in the last weeks</em></h2>	
		<div class="graph">
			<!-- Repository activity chart -->
			<?cs var:repository_activity.chart_info.embed_info ?>
			<!-- Repository activity data. -->
		</div>
		<div class="data-table">
			<table cellpadding="0" cellspacing="1">
				<?cs set:count = len(repository_activity.columns) ?>
				<thead>
					<tr>
						<th colspan="<?cs var:count+1 ?>"><?cs var:repository_activity.title?></th>
					</tr>
					<tr>
						<th rowspan="2">Weeks</th>
					
						<th colspan="<?cs var:count ?>">Authors</th>					
					</tr>
					<tr>
						<?cs each:autor = repository_activity.columns ?>
							<th><?cs var:autor ?></th>
						<?cs /each ?>
					</tr>
				</thead>
				<tbody>
					<?cs each:row = repository_activity.results ?>
					<tr>
						<td><?cs var:row.0 ?></td>
						<?cs each:data_serie = row.1 ?>
							<td><?cs var:data_serie ?></td>
						<?cs /each?>
					</tr>
					<?cs /each ?>
				</tbody>
			</table>
		</div>
		<div class="clear"></div>
	</div>
	<div class="report-wrapper">
		<h2>Ticket activity</h2>
		<div class="graph">
			<!-- Ticket activity chart -->
			<?cs var:ticket_activity.chart_info.embed_info ?>
			<!-- Ticket activity data. -->
		</div>
		<div class="data-table">
			<table cellpadding="0" cellspacing="1">
				<thead>
					<tr>
						<th colspan="0"><?cs var:ticket_activity.title?></th>
					</tr>
					<tr>
					<?cs each:label = ticket_activity.columns ?>
						<th> <?cs var:label ?></th>
					<?cs /each?>
					</tr>					
				</thead>
				<tbody>
					<?cs each:row = ticket_activity.results  ?>
					<tr>
						<td><?cs var:row.0?></td>
						<td><?cs var:row.1?></td>
					</tr>
					<?cs /each ?>
				</tbody>
			</table>
		</div>
		<div class="clear"></div>		
	</div>
	<div class="report-wrapper">
		<h2>Wiki activity: <em>Most active wiki authors in the last weeks</em></h2>
		<div class="graph">
			<!-- Wiki activity data. -->
			<?cs var:wiki_activity.chart_info.embed_info ?>
		</div>
		<div class="data-table">
			<!-- Wiki activity data. -->
			<table cellpadding="0" cellspacing="1">
				<?cs set:count = len(wiki_activity.columns) ?>
				<thead>
					<tr>
						<th colspan="<?cs var:count+1 ?>"><?cs var:wiki_activity.title?></th>
					</tr>
					<tr>
						<th rowspan="2">Week</th>	
						<th colspan="<?cs var:count ?>">Authors</th>					
					</tr>
					<tr>
						<?cs each:autor = wiki_activity.columns ?>
							<th><?cs var:autor ?></th>
						<?cs /each ?>
					</tr>
				</thead>
				<tbody>
					<?cs each:row = wiki_activity.results ?>
					<tr>
						<td><?cs var:row.0 ?></td>
						<?cs each:data_serie = row.1 ?>
							<td><?cs var:data_serie ?></td>
						<?cs /each?>
					</tr>
					<?cs /each ?>
				</tbody>
			</table>
		</div>
		<div class="clear"></div>		
	</div>
</div>
<script language="javascript" type="text/javascript">
	//Little hack to let the flash objects load before we send them our data.
	window.onload = function(){
		setTimeout("loadCharts()",100);
	};
</script>
<?cs include "footer.cs" ?>
