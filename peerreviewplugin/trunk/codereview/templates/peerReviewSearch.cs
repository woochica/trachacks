<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav"> 
	<h2>Peer Review Navigation</h2> 
	<ul>
		<li class="first">
			<?cs if:main == "yes" ?>My Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewMain ?>">My Code Reviews</a>
			<?cs /if ?>
		</li>
		<li>
			<?cs if:create == "yes" ?>Create a Code Review
			<?cs else ?><a href="<?cs var:trac.href.peerReviewNew ?>">Create a Code Review</a>
			<?cs /if ?>
		</li>
		<li <?cs if:manager == 0 ?>class="last"<?cs /if ?>>
			<?cs if:search == "yes" ?>Search Code Reviews
			<?cs else ?><a href="<?cs var:trac.href.peerReviewSearch ?>">Search Code Reviews</a>
			<?cs /if ?>
		</li>
		<?cs if:manager == 1 ?>
		<li class="last">
			<?cs if:option == "yes" ?>Manager Options
			<?cs else ?><a href="<?cs var:trac.href.peerReviewOptions ?>">Manager Options</a>
			<?cs /if ?>
		</li>
		<?cs /if ?>
	</ul> 
</div> 

 <p><b><h1>Code Review Search</h1></b></p>

<form id="searchReview" action="<?cs var:trac.href.peerReviewSearch ?>" method="post">
  	Code Review Name:
  	<input id="name" name="CodeReviewName" size="25" value="" type="text">
	<br>
	<br>
	Reviews after date -
	<select size="1" name="DateMonth" id="Month"
		onchange="resetDays(document.getElementById('Month').options[document.getElementById('Month').selectedIndex].value,
				document.getElementById('Year').options[document.getElementById('Year').selectedIndex].value)">
		<option value=0>Select...</option>
		<option value=01>January</option>
		<option value=02>February</option>
		<option value=03>March</option>
		<option value=04>April</option>
		<option value=05>May</option>
		<option value=06>June</option>
		<option value=07>July</option>
		<option value=08>August</option>
		<option value=09>September</option>
		<option value=10>October</option>
		<option value=11>November</option>
		<option value=12>December</option>
	</select>

	<span id="DaySpan">
		<select size="1" name="DateDay1" id="Day" onchange="setDateIndex();">
			<option value=0 selected>Select...</option>
		</select>
	</span>,
	<select size="1" name="DateYear" id="Year" 
		onchange="resetDays(document.getElementById('Month').options[document.getElementById('Month').selectedIndex].value,
				document.getElementById('Year').options[document.getElementById('Year').selectedIndex].value)">
		<option selected value="0">Select...</option>
		<?cs each:item = years ?>
			<option value=<?cs var:item ?>><?cs var:item ?></option>
		<?cs /each ?>
	</select>
	<br>
	<br>
	Status -
	<select size="1" name="Status" id="status">
		<option value="Select...">Select...</option>
		<option value="Open for review">Open for review</option>
		<option value="Reviewed">Reviewed</option>
		<option value="Ready for inclusion">Ready for inclusion</option>
		<option value="Closed">Closed</option>
	</select>
	<br>
	<br>
	Author -
	<select size="1" name="Author" id="author">
		<option>Select...</option>
		<?cs each:item = users ?>
			<option value="<?cs var:item ?>"><?cs var:item ?></option>
		<?cs /each ?>
	</select>

	<br>
	<br>
	<input type="hidden" name="doSearch" value="yes">
	<!-- used by javascript to get the current day selected -->
	<input type="hidden" name="DateDay" value="0" id="dayHolder">
  	<input value="Search" type="submit">
</form>
<?cs if:doSearch == "yes" ?>
	<b><h2>Search Results</h2></b>
	<table class="listing" id="myreviewlist">
		<thead>
			<tr>
				<td>Review</td>
				<td>Author</td>
				<td>Status</td>
				<td>Name</td>
				<td>Date Opened</td>
			</tr>
		</thead>
		<tbody>
			<?cs each:item = results ?>
				<!-- If there are results, display the result information return from Python -->
				<?cs if:item[2] != "" ?>
					<tr class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
						<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[0]?></a></td>
						<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[1]?></a></td>
						<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[2]?></a></td>
						<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[4]?></a></td>
						<td><a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:item[0]?>"><?cs var:item[3]?></a></td>
					</tr>
				<?cs /if ?>
				<?cs if:item[2] == "" ?>
					<tr>		
						<td><?cs var:item[0]?></td>
						<td><?cs var:item[1]?></td>
						<td><?cs var:item[2]?></td>
						<td><?cs var:item[4]?></td>
						<td><?cs var:item[3]?></td>
					</tr>
				<?cs /if ?>
			<?cs /each ?>
		</tbody>
	</table>
	<br>
<?cs /if ?>

<script language="Javascript">
var dateIndexSelected = "01";

var monthSelected = "<?cs var:searchValues.month ?>";
var daySelected = "<?cs var:searchValues.day ?>";
var yearSelected = "<?cs var:searchValues.year ?>";
var statusSelected = "<?cs var:searchValues.status ?>";
var authorSelected = "<?cs var:searchValues.author ?>";
var nameSelected = "<?cs var:searchValues.name ?>";

setSearchValues();

function setSearchValues()
{
	var monthSelect = document.getElementById('Month');
	var daySelect = document.getElementById('Day');
	var yearSelect = document.getElementById('Year');
	var authorSelect = document.getElementById('author');
	var statusSelect = document.getElementById('status');
	var textField = document.getElementById('name');
	nameSelected = nameSelected.replace(/&lt;/g, '<');
	nameSelected = nameSelected.replace(/&gt;/g, '>');
	nameSelected = nameSelected.replace(/&#34;/g, '"');
	nameSelected = nameSelected.replace(/&amp;/g, '&');
	textField.value = nameSelected;
	

	for(var i = 0; i < monthSelect.options.length; i++)
	{
		if(monthSelect.options[i].value == monthSelected)
		{
			monthSelect.options[i].selected = 'true';
			break;
		}
	}

	for(var i = 0; i < yearSelect.options.length; i++)
	{
		if(yearSelect.options[i].value == yearSelected)
		{
			yearSelect.options[i].selected = 'true';
			break;
		}
	}

	dateIndexSelected = daySelected;
	resetDays(monthSelected, yearSelected);

	for(var i = 0; i < authorSelect.options.length; i++)
	{
		if(authorSelect.options[i].value == authorSelected)
		{	
			authorSelect.options[0].selected = 'false';
			authorSelect.options[i].selected = 'true';
			break;
		}
	}
	for(var i = 0; i < statusSelect.options.length; i++)
	{
		if(statusSelect.options[i].value == statusSelected)
		{
			statusSelect.options[0].selected = 'false';
			statusSelect.options[i].selected = 'true';
			break;
		}
	}
}

function setDateIndex()
{
	dateIndexSelected = (document.getElementById('Day')).value;
	document.getElementById('dayHolder').value = dateIndexSelected;
}

function resetDays(month, year)
{
	var numDays = 0;
	var date = new Date();
	date.setFullYear(year, month - 1, 31);
	numDays = date.getDate();
	if(numDays < 4)
	{
		numDays = 31 - numDays;
	}
	setOptionText(document.getElementById('DaySpan'), numDays);
	setDateIndex();
}

function setOptionText(control, numDays)
{
	var innerHTML = '<select name=\"DateDay1\" id=\"Day\" onChange=\"setDateIndex();\">'
	innerHTML += '<option value = \"0\">Select...</option>';
	var day = '';

	for(var loop=1; loop <= numDays; loop++)
	{
		day = '';
		if(loop < 10)
		{
			day = '0'; //add a 0 to day so that all days are 2 digits - 01, 02, etc.
		}
		if(day + '' + loop == dateIndexSelected)
		{
			innerHTML += '<option selected value=' + day + loop + '>' + loop + '</option>\n';
		}
		else
		{
			innerHTML += '<option value=' + day + loop + '>' + loop + '</option>\n';
		}
	}

	innerHTML += '</select>';
	
	control.innerHTML = innerHTML;
}
</script>
<?cs include "footer.cs" ?>
