<?cs include "header.cs"?>
<?cs include "macros.cs"?>

    <form method="post" action="<?cs var:estimate.href ?>" >

      <div id="content" class="estimate">
	<div id="messages" >
	  <?cs each:item = estimate.messages ?>
            <div class="message" ><?cs var:item ?></div>
	  <?cs /each ?>
	</div>

	<table border="0" cellpadding="3" cellspacing="0" >
	  <tr>
	    <td ><label for="tickets">Ticket Numbers:</label></td>
	    <td><input id="tickets" type="text" /></td>
	  </tr>
	  <tr>
	    <td ><label for="rate">Rate</label></td>
	    <td><input id="rate" type="text" /></td>
	  </tr>
	  <tr>
	    <td ><label for="variability">Variability</label></td>
	    <td><input id="variability" type="text" /></td>
	  </tr>
	  <tr>
	    <td ><label for="communication">Communication</label></td>
	    <td><input id="communication" type="text" /></td>
	  </tr>
	</table>

	<script language="javascript" >
	  var cn = ADW.Controls.createNode;
	  var lineItems
	  function lineItemRow (lineitem){
	    var uid = function (str){
              return uid+lineitem.id;
	    }
	    var valFn = function(str){
	      if (lineitem[str]) return lineitem[str];
	      else return "";
	    }
	    return cn('tr', {},
	      cn('td', {},
                 cn('textarea', {id:uid("description")},
                   valFn('description'))),
    	      cn('td', {},
                 cn('input', {id:uid('low'), type:'text', value: valFn('low')})),

    	      cn('td', {},
                 cn('input', {id:uid('high'), type:'text', value: valFn('high')})),
    	      cn('td', {id:uid('ave')},
                 ))
	  }
	</script >

	<table border="0" cellpadding="3" cellspacing="0" >
	  <tr id="header">
	    <th>Description</th>
	    <th>Low </th>
	    <th>High </th>
	    <th>Ave </th>
	  </tr>
	  
	  <!-- Item Rows Go Here -->

	  <tr id="footer">
	    <th>Total:</th>
	    <td id="lowTotal" ></td>
	    <td id="highTotal"></td>
	    <td id="aveTotal"></td>
	  </tr>
	  <tr>
	    <th>Adjusted Hours:</th>
	    <td id="lowAdjusted"></td>
	    <td id="highAdjusted"></td>
	    <td id="aveAdjusted"></td>
	  </tr>
	  <tr>
	    <th>Cost:</th>
	    <td id="lowCost"></td>
	    <td id="highCost"></td>
	    <td id="aveCost"></td>
	  </tr>
	</table>

<!--
	<div>
	  <h3>Comment Preview</h3>
	  <div id="estimateoutput" >
	    
	  </div>
	</div>
-->
      </div>
    <input type="submit" >Save Estimate</input>   
    </form>
<?cs include "footer.cs"?>
    