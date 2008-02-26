<?cs include "newticket.cs" ?>

<div class="hidden" style="z-index:-99; visibility:hidden; position:static; top:-1000; right:-1000; "><?cs
  each:tt_item = tt_list ?>
	<textarea id=<?cs var:tt_item.name ?> ><?cs var:tt_item.text ?></textarea><?cs
  /each ?>
  
<textarea id="description_default"><?cs var:text ?></textarea>
<?cs var:text ?>
</div>

<script type="text/javascript">
{

	function onTypeChanged() { 
		descriptionElem = document.getElementById('description');
		defaultElem = document.getElementById('description_default');
		typeElem = document.getElementById('type');

		// update description textarea
		specElem = document.getElementById('description_' + typeElem.selectedIndex);
		descriptionElem.value = specElem.value ? specElem.value : defaultElem.value;

	}

	// add event listener
	addEvent(document.getElementById('type'), 'change', onTypeChanged); 
	addEvent(window, 'load', onTypeChanged); 

	// set focus
	document.getElementById('summary').focus()
}
</script>


