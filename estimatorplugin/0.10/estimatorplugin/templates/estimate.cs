<?cs include "header.cs"?>
<?cs include "macros.cs"?>

    <form method="post" action="<?cs var:estimate.href ?>" >
      <input type="hidden" name="id" value="<?cs var:estimate.id?>"/>
      <div id="content" class="estimate">
	<div id="messages" >
	  <?cs each:item = estimate.messages ?>
            <div class="message" ><?cs var:item ?></div>
	  <?cs /each ?>
	</div>

	<table border="0" cellpadding="3" cellspacing="0" id="estimateParams" >
	  <tr>
	    <td class="fieldLabel" ><label for="tickets">Ticket Numbers:</label></td>
	    <td><input id="tickets" name="tickets" type="text"
		      value="<?cs var:estimate.tickets ?>"
		      onkeydown="return enterMeansNothing(event)" /></td>
	  </tr>
	  <tr>
	    <td class="fieldLabel" ><label for="rate">Rate:</label></td>
	    <td><input id="rate" name="rate" type="text" onkeyup="runCalculation()"
		      value="<?cs var:estimate.rate?>"
		      onkeydown="return enterMeansNothing(event)" /></td>
	  </tr>
	  <tr>
	    <td class="fieldLabel" ><label for="variability">Variability:</label></td>
	    <td><input id="variability" name="variability" type="text" onkeyup="runCalculation()"
		      value="<?cs var:estimate.variability?>"
		      onkeydown="return enterMeansNothing(event)" /></td>
	  </tr>
	  <tr>
	    <td class="fieldLabel" ><label for="communication">Communication:</label></td>
	    <td><input id="communication" name="communication" type="text" onkeyup="runCalculation()"
		      value="<?cs var:estimate.communication?>"
		      onkeydown="return enterMeansNothing(event)" /></td>
	  </tr>
	</table>


	<table border="0" cellpadding="3" cellspacing="1" id="estimateBody" width="660" >
	  <tr id="lineItemheader" >
	    <th>Description</th>
	    <th>Low </th>
	    <th>High </th>
	    <th>Ave </th>
	    <th></th>
	  </tr>


	  <tr id="lineItemFooter">
	    <th class="fieldLabel" >Total:</th>
	    <td id="lowTotal" class="numberCell" ></td>
	    <td id="highTotal" class="numberCell"></td>
	    <td id="aveTotal" class="numberCell"></td>
	    <td></td>
	  </tr>
	  <tr>
	    <th class="fieldLabel">Adjusted Hours:</th>
	    <td id="lowAdjusted" class="numberCell" ></td>
	    <td id="highAdjusted" class="numberCell" ></td>
	    <td id="aveAdjusted" class="numberCell" ></td>
	    <td></td>
	  </tr>
	  <tr>
	    <th class="fieldLabel">Cost:</th>
	    <td id="lowCost" class="numberCell" ></td>
	    <td id="highCost" class="numberCell" ></td>
	    <td id="aveCost" class="numberCell" ></td>
	    <td></td>
	  </tr>
	</table>

	<button id="newrow" onclick="newLineItem();return false;">new row</button>
	<button onclick="runCalculation();return false;">refresh calculations</button>
	<br /><br />
	<input type="submit" value="Save Estimate" onclick="runCalculation();this.form.submit();return false;" />
	<div>
	    <h3>Comment Preview</h3>
	    <div id="estimateoutput" >

	    </div>
	    <textarea id="comment" name="comment" style="display:none;"></textarea>
	</div>

	<script language="javascript" >
	   var lineItems = <?cs var:estimate.lineItems?>;
	   loadLineItems();
	   if(lineItems.length == 0) newLineItem();
	</script >
      </div>

    </form>
<?cs include "footer.cs"?>
    