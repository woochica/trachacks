/*
*Hides the Tabelle of  all Entryrow by changing the visibility of an
* parent elment by the id hiddenbudgettable
*/
function hideTable(){
	document.getElementById('hiddenbudgettable').style.visibility = "hidden";
}

/*
* Adding a new entry row to the defined tbody table element at the bottom of the list
*/
function addBudgetRow(){
	// Getting the values of the types - select by reading an hidden
	// Element with the id selectTypes in the html page
	if (document.getElementById('selectTypes') != null)
		var types = document.getElementById('selectTypes').innerHTML;
		types = types.split(';');
	// Getting the name-select values from html
	if (document.getElementById('selectNames') != null)
		var names = document.getElementById('selectNames').innerHTML;
		names = names.split(';');
	// Chane hidden tbody elment to be visible
	document.getElementById('hiddenbudgettable').style.visibility = "visible";
	var tBodyContainer=document.getElementById('budget_container');
	// initialise the rowcounter by the current amount of rows
	var trElements = tBodyContainer.getElementsByTagName('tr');
	var rowCounter = 1;
	if (trElements && trElements.length > 0) {
		rowCounter = trElements[trElements.length - 1].id.split(':')[1];
		rowCounter++;
	}
	var tableRow=document.createElement('tr');
	//Amount of Columns, may should be given by function call
	var columnCount=6;
	tableRow.id='row:'+rowCounter;
	tBodyContainer.appendChild(tableRow);
	//Adding column by column to the row element
	for(column = 1; column <= columnCount; column++){
		var td =document.createElement('td');
		tableRow.appendChild(td);
		var columnElement;
		// Select TYPES Column Position 2
		if(column == 2) {
			columnElement = getSelect(types);
		// Select NAME Column Position 1
		} else if(column==1) {
			columnElement = getSelect(names);
		//Non Select, just an input text field
		} else {
			columnElement=document.createElement('input');
			columnElement.size = 10;
		}
		
		if (column == 6) {
			columnElement.size = 20;
		}
		columnElement.name='GSfield:'+rowCounter+':'+column;
		td.appendChild(columnElement);
	}
	// Adding a Delete Button to the end of the row
	deleteButtonElement = document.createElement('td');
	deleteButtonElement.innerHTML = "<button type='button' name='deleteRow"+rowCounter+"' onclick='deleteRow(" + rowCounter + ")'>[-]</button>";
	tableRow.appendChild(deleteButtonElement);
}

/*
*Creates a new Select Element with the optionsvalues which were given
* by the submitted Array
*/
function getSelect(optionArray){
	if (optionArray == null)
		return null;
	
	var columnElement=document.createElement('select');
	for(arrayPosition = 0; arrayPosition < optionArray.length;arrayPosition++){
		newOption =document.createElement('option');
		newOption.text=optionArray[arrayPosition];
		try {//standards compliant; doesn't work in IE
			columnElement.add(newOption, null); 
		}
		catch(ex) { //just ie
			columnElement.add(newOption, columnElement.selectedIndex); 
		}
	}
	return columnElement
}


/*
* Marks a Row, by the given rowid, as to delete by adding 
* a style attribut visibility by the value none to the parent
* tr Element. All fields additionally will gets an Prefix DEL on
* the beginning of the Name: NewName = DEL + oldName
* The Prefix DEL is necessary to identify deleted rows in 
* further processing performed by the python plugin
*/
function deleteRow(row){
	if (row < 0)
		return;
		
	var rowid = "row:"+row;
	var rowElement = document.getElementById(rowid);
	rowElement.style.display = "none";
	var selectElements = rowElement.getElementsByTagName("select");
	var inputElements = rowElement.getElementsByTagName("input");
	for(var i = 0; i < selectElements.length; i++){
		selectElements[i].name =('DEL'+selectElements[i].getAttribute('name'));
	}
	for(var i = 0; i < inputElements.length; i++){
		inputElements[i].name =('DEL'+inputElements[i].getAttribute('name'));
	}
	
	var rowElements =document.getElementById('container').getElementsByTagName('tr');
	// This logic ist responsible for hidding the complete tbody element, if no further
	// row ist visible or rather not deleted
	var hiddenCounter = 1;
	for(var i = 0; i < rowElements.length; i++){
		if (rowElements[i].style["display"].length > 0){
			hiddenCounter++;
		}
	}
	if(hiddenCounter >rowElements.length){
		hideTable();
	}
	
}