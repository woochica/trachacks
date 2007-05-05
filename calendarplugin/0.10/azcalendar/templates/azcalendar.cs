<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>
<?cs include "azdays.cs" ?>
<?cs include "azweekcal.cs" ?>
<?cs include "azmonthcal.cs" ?>

<div id="content" class="azcalendar">
    <h1>Calendar</h1>
    <!-- img src="<?cs var:chrome.href ?>/hw/images/aztec.jpg" / -->

    <ul class='azcalcontrols'>
        <li class='azcalcontrol'><a href='?date=<?cs var:azcalendar.prev_date ?>'>prev month</a></li>
        <li class='azcalcontrol'><a href='?date=<?cs var:azcalendar.today_date ?>'>today</a></li>
        <li class='azcalcontrol'><a href='?date=<?cs var:azcalendar.next_date ?>'>next month</a></li>
    </ul>

    <div class='azmonthcalscroll'>
	<table class='azmonthcal-container'><tr>
	    <?cs each:month = azcalendar.months ?>
		<td class='azmonthcal-container'>
	    	    <?cs call:azmonthcal("azcalendar", month.year, month.month, month.firstday, month.numdays, month.impdays) ?>
	    	</td>
	    <?cs /each ?>
	</tr></table>
    </div>

    <?cs call:azweekcal("azcalendar", azcalendar.events) ?>
</div>

<?cs include "footer.cs" ?>
