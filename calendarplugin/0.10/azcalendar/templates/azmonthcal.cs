<?cs def:azmonthcal(urlbase, year, month, firstday, numdays, important) ?>
    <table class='azmonthcal'>
    <tr class='head'><td colspan="7" class='title'><?cs call:monthname(month) ?><?cs var:year ?></td></tr>

    <?cs set:tmp.rows = (#firstday + #numdays) / #7 ?>
    <?cs if:(tmp.rows * #7) < (#firstday + #numdays) ?><?cs set:tmp.rows = tmp.rows + 1 ?><?cs /if ?>

    <tr class='days'>
	<?cs loop:day = #0, #6, #1 ?>
    	    <td class='dayname'><?cs call:dayname(day) ?></td>
	<?cs /loop ?>
    </tr>

    <?cs set:tmp.urlbase = urlbase + '?date=' + year ?>
    <?cs set:tmp.month = #month + 1 ?>
    <?cs if:tmp.month < 10 ?><?cs set:tmp.urlbase = tmp.urlbase + '0' ?><?cs /if ?>
    <?cs set:tmp.urlbase = tmp.urlbase + tmp.month ?>

    <?cs set:tmp.idx = 0 ?>
    <?cs loop:row = #1, #tmp.rows, #1 ?>
	<tr class='cal'>
	    <?cs loop:day = #0, #6, #1 ?>
	        <?cs set:tmp.idx = #tmp.idx + 1 ?>
		<?cs if:tmp.idx <= #firstday ?>
		    <td class='empty'>&nbsp;</td>
		<?cs elif:tmp.idx <= (#firstday + #numdays) ?>
		    <?cs set:tmp.day = tmp.idx - #firstday ?>

		    <?cs set:tmp.url = tmp.urlbase ?>
		    <?cs if:tmp.day < 10 ?><?cs set:tmp.url = tmp.url + '0' ?><?cs /if ?>
		    <?cs set:tmp.url = tmp.url + tmp.day ?>

		    <td <?cs if:important[tmp.day] ?>class='<?cs var:important[tmp.day] ?>'
			<?cs else ?>class='day'
			<?cs /if ?>>
		    <a class='show' href='<?cs var:tmp.url ?>'><?cs var:tmp.day ?></a>
		    <!-- a class='add' href='<?cs var:tmp.url ?>'>+</a -->
		    </td>
		<?cs else ?>
		    <td class='empty'>&nbsp;</td>
		<?cs /if ?>
	    <?cs /loop ?>
	</tr>
    <?cs /loop ?>

    <?cs loop:row = #tmp.rows + 1, #6, #1 ?>
	<tr class='empty'>
	    <td class='empty' colspan='7'>&nbsp;</td>
	</tr>
    <?cs /loop ?>

    </table>
<?cs /def ?>
