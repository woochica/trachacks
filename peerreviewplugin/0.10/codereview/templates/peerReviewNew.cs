<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<style>
<!--
table.code th.addFileNums {
        width: 4em;
}
//-->
</style>

<!-- Top Navigation Bar -->
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

<p><h1>Create a New Code Review</h1></p>

<h2>Step 1: Choose a name for this review.</h2><br>

<!-- CodeReview name is empty if new, with previous name is resubmitted -->
<form method="post" action="<?cs var:trac.href.peerReviewNew ?>" onsubmit="return validateInput(this);">
Name: <input type="text" name="Name" MAXLENGTH="50" value="<?cs var:name?>"><br>

<h2>Step 2: Select the sections to be reviewed.</h2><br>
<!-- Displays the file browser -->
<span id="browserArea"></span>
<table class="listing" id="myfilelist">
	<thead>
		<tr>
			<td>Filename (Click to remove)</td>
			<td>Start Line</td>
			<td>End Line</td>
			<td>Rev</td>
		</tr>
	</thead>

<!-- Display an empty file list if it's a new CodeReview, display previous list if resubmitted -->
	<tbody id = "myfilebody">
	<?cs if:new == "yes" ?>
		<tr id = "nofile" class="even">
			<td>No files have been added to the code review.</td>
			<td></td>
			<td></td>
			<td></td>
		</tr>
	<?cs else ?>
		<?cs each:item = prevFiles ?>
			<tr id="<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>id" class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
				<td value="<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>"><a href="javascript:removefile('<?cs var:item[0] ?>,<?cs var:item[1] ?>,<?cs var:item[2] ?>,<?cs var:item[3] ?>')"><?cs var:item[0] ?></a></td>
				<td><?cs var:item[2] ?></td>
				<td><?cs var:item[3] ?></td>
				<td><?cs var:item[1] ?></td>
			</tr>
		<?cs /each ?>
	<?cs /if ?>
	</tbody>
</table><br><br>

<h2>Step 3: Select reviewers for your review.</h2><br>

<!-- Display a full reviewer drop-down list if it's a new CodeReview, display unassigned reviewers if resubmitted -->
<?cs if:new == "yes" ?>
	<select id="Reviewers">
		<?cs each:item = users ?>
			<option value="<?cs var:item ?>"><?cs var:item ?></option>
		<?cs /each ?>
	</select>
<?cs else ?>
	<?cs if:emptyList == 0 ?>
		<select id="Reviewers">
			<?cs each:item = notPrevUsers ?>
				<option value="<?cs var:item ?>"><?cs var:item ?></option>
			<?cs /each ?>
		</select>
	<?cs else ?>
		<select id="Reviewers">
				<option value="-1">--All users exhausted--</option>
		</select>
	<?cs /if ?>
<?cs /if ?>

<input <?cs if:emptyList==1 ?>disabled<?cs /if ?> id="adduserbutton" type="button" onclick="adduser()" value="Add user"><br>

<!-- Display an empty file list if it's a new CodeReview, display previous list if resubmitted -->
<?cs if:new == "yes" ?>
		<table class="listing" id="myuserlist">
		<thead>
			<tr>
				<td>Username (Click to remove)</td>
			</tr>
		</thead>
		<tbody id = "myuserbody">
			<tr id = "No Users" class="even">
				<td>No users have been added to the code review.</td>
			</tr>
		</tbody>
	</table>
<?cs else ?>
	<table class="listing" id="myuserlist">
		<thead>
			<tr>
				<td>Username (Click to remove)</td>
			</tr>
		</thead>
		<tbody id = "myuserbody">
			<?cs each:item = prevUsers ?>
				<tr id="<?cs var:item ?>id" class="<?cs if:name(item) % #2 ?>even<?cs else ?>odd<?cs /if ?>">
					<td value="<?cs var:item ?>"><a href="javascript:removeuser('<?cs var:item ?>')"><?cs var:item ?></a></td>
				</tr>
			<?cs /each ?>
		</tbody>
	</table>
<?cs /if ?>
<br><br>

<h2>Step 4: Write general notes and instructions for the reviewers. (Optional)</h2>
<!-- Display an empty notes area if it's a new CodeReview, display previous notes if resubmitted -->
	<textarea name="Notes" cols=60 rows=8><?cs if:new != "yes" ?><?cs var:notes ?><?cs /if ?></textarea>

<br><br>
<?cs if:oldid > -1 ?>
<input type="hidden" name="oldid" value="<?cs var:oldid ?>">
<?cs /if ?>
<input type="hidden" name="ReviewersSelected" id="ReviewersSelected" value="<?cs if:new != "yes" ?><?cs var:reviewers ?><?cs /if ?>">
<input type="hidden" name="FilesSelected" id="FilesSelected" value="<?cs if:new != "yes" ?><?cs var:files ?><?cs /if ?>">
<input type="hidden" name="reqAction" value="createCodeReview">
<input type="submit" name="Next" value="<?cs if:new == "yes" ?>Add Code Review<?cs else ?>Resubmit Code Review<?cs /if ?>">
<br>
</form>

<script type="text/javascript">
<!--

var browserCallback = "<?cs var:trac.href.peerReviewBrowser ?>";
var GLOBAL_lineStart = -1;
var GLOBAL_lineEnd = -1;

//Forces Internet Explorer to display a scrollbar
function resetInnerDivSize()
{
    var innerDiv = document.getElementById('preview');
    if(innerDiv != null)
    {
   	innerDiv.style.height = "";
	if(innerDiv.clientHeight >= 400)
	{
	    innerDiv.style.height = "400px";
	}
	else if(innerDiv.clientHeight > 0)
	{
	    innerDiv.style.height = innerDiv.offsetHeight + "px";
	}
    }
}

//Colorizes the tables according to Trac standards
function colorTable(txt){
	var table = document.getElementById(txt);
	var loop = 0;
	for (; loop < table.rows.length; loop++) {
		var row = table.rows[loop];
		if (loop % 2 == 0) {
			row.className = 'odd';
		} else {
			row.className = 'even';
		}
	}
}

// adds a row to the table with txt as the text in the row
function addrow(txt)
{
	var tbl = document.getElementById('myuserbody');
	var lastRow = tbl.rows.length;
	var row = tbl.insertRow(lastRow);

	// We will append the new username to the ReviewersSelected hidden input
	var users = document.getElementById('ReviewersSelected');
	//document.setElementByName('ReviewersSelected', users + "#" + txt);
	users.setAttribute('value', users.value + txt + "#");
  
	row.id = txt + 'id';
	var cellLeft = row.insertCell(0);
	cellLeft.setAttribute('value', txt);
	cellLeft.innerHTML = "<a href=\"javascript:removeuser('" + txt + "')\">" + txt + "</a>";
	row.appendChild(cellLeft);
}

// takes a user from the dropdown, adds them to the table, and deletes from the dropdown
function adduser()
{
	var dropdown = document.getElementById('Reviewers');
	var tbl = document.getElementById('myuserbody');

	if((tbl.rows.length == 1) && (tbl.rows[0].getAttribute("id") == "No Users")) 
		checkEmpty(1, 'myuserbody');

	addrow(dropdown.options[dropdown.selectedIndex].text);
	dropdown.options[dropdown.selectedIndex] = null;
	
	if (dropdown.options.length == 0) {
		// No users left
		dropdown.options[0] = new Option('--All users exhausted--','-1');
		document.getElementById("adduserbutton").disabled = true;
		document.getElementById("adduserbutton").style.color = "";
	}
			
	colorTable('myuserbody');
}

// takes a user from the table, adds them to the dropbox, and deletes from the table
function removeuser(txt) {
	var dropdown = document.getElementById('Reviewers');
	
	if (dropdown.options[0].value == '-1') {
		dropdown.options[0] = new Option(txt, '0');
		document.getElementById("adduserbutton").disabled = false;
		document.getElementById("adduserbutton").style.color = "#000000";
	} else {
		dropdown.options[dropdown.options.length] = new Option(txt, '0');
	}

    //remove the user from the post value
    var users = document.getElementById('ReviewersSelected');
    var tokens = users.value.split("#");    
    var newusers = "";
    for (var i=0; i<tokens.length-1; i++) {
        if (tokens[i] == txt)
            continue;
        newusers += tokens[i] + "#";
    }

    users.setAttribute('value', newusers);
    
	// delete the row containing the txt from the table
	var table = document.getElementById('myuserbody');

	// remove row
	var loop = 0;
	for (loop = 0; loop < table.rows.length; loop++) {
		
		var row = table.rows[loop];
		var cell = row.cells[0];
		if (row.id == txt + 'id') {
			table.deleteRow(loop);
			loop--;
			break;
		}
	}

	colorTable('myuserbody');
	
	if (table.rows.length == 0) 
		checkEmpty(0, 'myuserbody');
}

// Checks for an empty table to label it as such
function checkEmpty(num, itemID) {
	var table = document.getElementById(itemID);

	switch (num) {
    		case 0:
			//Table is now empty 
			table.insertRow(0);
			table.rows[0].setAttribute('id', "No Users");
			table.rows[0].className = 'even';
			var cellLeft = table.rows[0].insertCell(0);
			cellLeft.innerHTML = "No users have been added to the code review.";
			table.rows[0].appendChild(cellLeft);
			break;
    		case 1:
			//Need to add things to the table, get rid of No Users row
			table.deleteRow(0);
			break;
    		default :
			alert("Error in CheckEmpty function");
	}
}

function validateInput(form) {
	if (form.Name.value == "") {
        	alert("You must specify a code review name.");
		return false;
    	}

    	if (form.FilesSelected.value == "") {
		alert("You must select at least one file.");
		return false;
	}
	
	if (form.ReviewersSelected.value == "") {
        	alert("You must select at least one user.");
		return false;
    	}

	return true;
}

//Define XML object in terms of IE or Gecko engine
function createXMLObject(){
    var xmlObj = null;
    if(window.XMLHttpRequest){
        xmlObj = new XMLHttpRequest();
    } else if(window.ActiveXObject){
        xmlObj = new ActiveXObject("Microsoft.XMLHTTP");
    }

    return xmlObj;
}

//Prepares place for browser in HTML
function placeBrowser(contents)
{
    var place = document.getElementById('browserArea');
    place.innerHTML = contents;
    processBrowser(place);
    resetInnerDivSize();
    GLOBAL_lineStart = -1;
    GLOBAL_lineEnd = -1;
}


//Controls the file browser's click-throughs to ensure the file browser does not close
function processBrowser(parent)
{
    for(var i=0; i< parent.childNodes.length; i++)
        {
            processBrowser(parent.childNodes[i]);
        }

    if(parent.tagName == "A")
        {
            if(parent.href.indexOf("peerReviewBrowser") >= 0)
                {
                    parent.href = "javascript:getBrowser('" + parent.href + "')";
                }
        }
}

//Changes the revision displayed in the file browser
function switchRev(e)
{
    if(e.keyCode == 13 || e.keyCode == 3)
    {
        getBrowser(browserCallback + '?rev=' + document.getElementById('rev').value);
    	if(e.stopPropagation)
	  e.stopPropagation();
    	e.cancelBubble = true;
	if(e.preventDefault)
	  e.preventDefault();
	event.returnValue = false;
        event.cancel = true;
    }
}

//Performs the callback to the server with the clicked links in the browser
function getBrowser(url){
    var place = document.getElementById('browserArea');
    place.innerHTML = "Loading....";
    resetInnerDivSize()
    
    var xmlObj = createXMLObject();
    if(xmlObj != null){
        xmlObj.onreadystatechange = function(){
            if(xmlObj.readyState == 4){
                placeBrowser(xmlObj.responseText);
            }
        }
        xmlObj.open ('GET', url, true);
        xmlObj.send ('');
    }
    lastPick = null;
}

function lineEnter(e)
{
   if(e.keyCode == 13 || e.keyCode == 3)
    {
	addButtonEnable();
    	if(e.stopPropagation)
	  e.stopPropagation();
	if(e.preventDefault)
	  e.preventDefault();
    	e.cancelBubble = true;
	event.returnValue = false;
        event.cancel = true;
    }
}

// Sets the line number ranges in the file browser
function setLineNum(num)
{
	var box1 = document.getElementById('lineBox1');
	var box2 = document.getElementById('lineBox2');
	if(box1 == null || box2 == null)
        	return;
	if(lastPick == null)
        {
                box1.value = num;       
       	}
        else if(lastPick >= num)
        {
        	box1.value = num;
                box2.value = lastPick;
        }
        else if(lastPick < num)
        {
	        box1.value = lastPick;
                box2.value = num;
        }
        lastPick = num;
        addButtonEnable();
}

//Add a file to the file structure in the database
function addFile(filepath)
{
	var tbl = document.getElementById('myfilebody');
	
	if ((tbl.rows.length == 1) && (tbl.rows[0].getAttribute("id") == "nofile")) {
		tbl.deleteRow(0);
	}
	
	var lastRow = tbl.rows.length;
	
	var box1 = document.getElementById('lineBox1');
    	var box2 = document.getElementById('lineBox2');
	var revBox = document.getElementById('fileRevVal');

	var saveLine = filepath + "," + revBox.value + "," + box1.value + "," + box2.value;

	if(document.getElementById(saveLine + 'id') != null) {
		alert("Specified combination of filename, revision, and line numbers is already included in the file list.");
		return;
	}
	
	var row = tbl.insertRow(lastRow);

	var files = document.getElementById('FilesSelected');
	files.setAttribute('value', files.value + saveLine + "#");

	//Create the entry in the actual table in the page
	  
	row.id = saveLine + 'id';
	var cellLeft = row.insertCell(0);
	cellLeft.innerHTML = "<a href=\"javascript:removefile('" + saveLine + "')\">" + filepath + "</a>";
	cellLeft.setAttribute('value', saveLine);
	row.appendChild(cellLeft);
	cellLeft = row.insertCell(1);
	cellLeft.innerHTML = box1.value;
	row.appendChild(cellLeft);
	cellLeft = row.insertCell(2);
	cellLeft.innerHTML = box2.value;
	row.appendChild(cellLeft);
	cellLeft = row.insertCell(3);
	cellLeft.innerHTML = revBox.value;
	row.appendChild(cellLeft);
		
	colorTable('myfilebody');
}

//Remove the file from the struct

function removefile(txt) {
    //remove the file from the post value
    var files = document.getElementById('FilesSelected');
    var tokens = files.value.split("#");    
    var newfiles = "";
    for (var i=0; i<tokens.length-1; i++) {
        if (tokens[i] == txt)
            continue;
        newfiles += tokens[i] + "#";
    }

    files.setAttribute('value', newfiles);
    
	// delete the row containing the txt from the table
	var filetable = document.getElementById('myfilelist');

	var loop = 0;
	for (loop = 0; loop < filetable.rows.length; loop++) {
		var row = filetable.rows[loop];
		var cell = row.cells[0];
		if (row.id == txt + 'id') {
			filetable.deleteRow(loop);
			loop--;
			break;
		}
	}

	colorTable('myfilebody');
	
	//Remove the entry from the table in the HTML

	var tbl = document.getElementById('myfilebody');
	if (tbl.rows.length == 0){
		tbl.insertRow(0);
		tbl.rows[0].setAttribute('id', "nofile");
		var cellLeft = tbl.rows[0].insertCell(0);
		cellLeft.innerHTML = "No files have been added to the code review.";
		tbl.rows[0].appendChild(cellLeft);
		cellLeft = tbl.rows[0].insertCell(1);
		cellLeft.innerHTML ="";
		tbl.rows[0].appendChild(cellLeft);
		cellLeft = tbl.rows[0].insertCell(2);
		cellLeft.innerHTML ="";
		tbl.rows[0].appendChild(cellLeft);
		cellLeft = tbl.rows[0].insertCell(3);
		cellLeft.innerHTML ="";
		tbl.rows[0].appendChild(cellLeft);
	}
}
               
//Enable the Add File button when a correct file, revision, and line number range is chosen

function addButtonEnable()
{
	var i = 1;
	var temp = null;
        var box1 = document.getElementById('lineBox1');
        var box2 = document.getElementById('lineBox2');
	var addButton = document.getElementById('addFileButton');

        if(box1 == null || box2 == null || addButton == null)
        	return;

	addButton.disabled = true;
	addButton.style.color = "";
	
	if(GLOBAL_lineStart != -1 && GLOBAL_lineEnd != -1)
	{
		for(i = GLOBAL_lineStart; i<= GLOBAL_lineEnd; i++)
		{
        		temp = document.getElementById('L' + i);
			if(temp != null)
		               	temp.innerHTML = "<a href=\"javascript:setLineNum(" + i + ")\">" + i + "</a>";
		}
        }
	
	GLOBAL_lineStart = -1;
	GLOBAL_lineEnd = -1;

	if(box1.value == "" || box2.value == "" || isNaN(box1.value) || isNaN(box2.value))
		return;

	var start = parseInt(box1.value);
	var end = parseInt(box2.value);
	if(start < 1)
		start = 1;
	if(end < 1)
		end = 1;
	if(start > end)
	{
		i = start;
		start = end;
		end = i;
	}
	
	if(document.getElementById('L' + start) == null)
		return;
	
        for(i=start; i<=end; i++)
        {
        	temp = document.getElementById('L' + i);
                if(temp != null)
		{
                	temp.innerHTML = "<a href=\"javascript:setLineNum(" + i + ")\"><font color=red><b>" + i + "</b></font></a>"
		}
		else
		{
			end = i-1;
		}
        }

	GLOBAL_lineStart = start;
	GLOBAL_lineEnd = end;

	box1.value = start;
	box2.value = end;

     	addButton.disabled = false;
	addButton.style.color = "#000000";
}

getBrowser(browserCallback);

//-->
</script>

<?cs include "footer.cs" ?>
