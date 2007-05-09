<?cs
def:azweekcal_daynamecell(dayevents, span) ?>
		    <td class='dayname' rowspan='<?cs var:span ?>'>
			<div class='dow'><?cs call:dayname(name(dayevents)) ?></div>
			<div class='date'><?cs var:dayevents.date.day + '.' + dayevents.date.month + '.' + dayevents.date.year ?></div>
		    </td><?cs
/def ?><?cs

def:azweekcal_pluscell(urlbase, date) ?><?cs
    set:tmp.urlbase = urlbase + '/add?date=' + date.year ?><?cs
    if:#date.month < 10 ?><?cs set:tmp.urlbase = tmp.urlbase + '0' ?><?cs /if ?><?cs
    set:tmp.urlbase = tmp.urlbase + date.month ?><?cs
    if:#date.day < 10 ?><?cs set:tmp.urlbase = tmp.urlbase + '0' ?><?cs /if ?><?cs
    set:tmp.urlbase = tmp.urlbase + date.day ?>
		    <td class='plus'><a href='<?cs var:tmp.urlbase ?>'>+</a></td><?cs
/def ?><?cs

def:azweekcal_evtcell(urlbase, event) ?><?cs
    set:tmp.title = event.time_begin + ' - ' + event.time_end ?><?cs
    set:tmp.urlbase = urlbase + '/event?id=' + event.id ?><?cs
    set:tmp.span = event.brd_end - event.brd_begin ?><?cs
    if:tmp.span >= 4 ?><?cs
        set:tmp.show = event.title ?><?cs
    else ?><?cs
        set:tmp.title = tmp.title + ': ' + event.title ?><?cs
        set:tmp.show = '...' ?><?cs
    /if ?>
			<td class='<?cs var:event.priority ?>' colspan='<?cs var:tmp.span ?>' title='<?cs var:tmp.title ?>'>
			    <a class='show' href='<?cs var:tmp.urlbase ?>'><?cs var:tmp.show ?></a>
			</td><?cs
/def ?><?cs

def:azweekcal(urlbase, events) ?>
    <div class='azweekcalscroll'>
	<table class='azweekcal'>
	    <!-- HEADER -->
	    <tr class='head'>
		<td class='dayname'>&nbsp;</td>
		<?cs
		loop:hr = #0, #23, #1
		    ?><td colspan='<?cs var:azcalendar.div ?>'><?cs var:hr ?> - <?cs var:hr+#1 ?></td><?cs
		/loop ?>
	    </tr>

	    <?cs each:dayevents = events ?>
	    <tr class='gutter'><td /><?cs
    		    loop:hr = #0, #23, #1 ?><?cs
		        loop:sub = #1, #azcalendar.div, #1 ?><td /><?cs /loop ?><?cs
		    /loop
	    ?></tr>
		<?cs
		set:tmp.have_plus = 0 ?><?cs
		set:tmp.have_day = 0 ?><?cs
		set:tmp.extra_space_for_plus = 1 ?><?cs

    		each:line = dayevents.events ?><?cs
		    set:tmp.line_has_space_for_plus = 1 ?><?cs
		    each:event = line ?><?cs
		        if:event.brd_begin <= 1?><?cs
			    set:tmp.line_has_space_for_plus = 0 ?><?cs
			/if ?><?cs
		    /each ?><?cs
    		    if:tmp.line_has_space_for_plus == 1 ?><?cs
    		    	set:tmp.extra_space_for_plus = 0 ?><?cs
    		    /if ?><?cs
		/each ?><?cs

		set:tmp.first_line = 1 ?><?cs
    		each:line = dayevents.events ?>
		    <tr class='line'><?cs
		        if:tmp.first_line ?><?cs
			    call:azweekcal_daynamecell(dayevents, subcount(dayevents.events) + tmp.extra_space_for_plus) ?><?cs
			    set:tmp.have_day = 1 ?><?cs
			    set:tmp.first_line = 0 ?><?cs
			/if ?><?cs
			set:tmp.last_end = 0 ?><?cs

			set:tmp.first_event = 1 ?><?cs
			each:event = line ?><?cs
    			    if:tmp.have_plus == 0 && tmp.first_event && event.brd_begin > 1 ?><?cs
				set:tmp.last_end = 1 ?><?cs
				set:tmp.have_plus = 1 ?><?cs
				set:tmp.first_event = 0 ?><?cs
				call:azweekcal_pluscell(urlbase, dayevents.date) ?><?cs
    			    /if ?><?cs
			    set:tmp.space = event.brd_begin - tmp.last_end ?><?cs
			    if:tmp.space > 0 ?>
			        <td class='empty' colspan='<?cs var:tmp.space ?>'>&nbsp;</td><?cs
			    /if ?><?cs call:azweekcal_evtcell(urlbase, event) ?><?cs
			    set:tmp.last_end = event.brd_end ?><?cs
			/each ?><?cs

			set:tmp.space = azcalendar.div * 24 - tmp.last_end ?><?cs
			if:tmp.space > 0
			    ?><td class='empty' colspan='<?cs var:tmp.space ?>'>&nbsp;</td><?cs
			/if ?>
		    </tr><?cs
		/each ?><?cs

    		if:subcount(dayevents.events) == 0 || tmp.have_plus == 0
		    ?><tr class='line'><?cs
		        if:tmp.have_day == 0 ?><?cs
			    call:azweekcal_daynamecell(dayevents, 1) ?><?cs
			else ?><?cs
			/if ?><?cs
			call:azweekcal_pluscell(urlbase, dayevents.date)
    			?><td class='space' colspan='95'>&nbsp;</td>
		    </tr><?cs
		/if ?><?cs

	     /each ?>
	</table>
    </div><?cs
/def ?>
