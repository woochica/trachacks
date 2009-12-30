<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

<div id="ctxtnav" class="nav">
<ul>
	<li><img src="<?cs var:chrome.href ?>/wikinavmap/images/link.png"><a href="#" id="linkhere">Link to this page</a></li>
	<li><img class="icon" src="<?cs var:chrome.href ?>/wikinavmap/images/overview.png"><a href="#" onclick="toggleOverview(this);" id="toggleOverview">hide overview</a></li>
	<li><img class="icon" src="<?cs var:chrome.href ?>/wikinavmap/images/configure.png"><a href="#configure_window" onclick="showModal('configure_window');">Configure</a></li>
	<li><img class="icon" src="<?cs var:chrome.href ?>/wikinavmap/images/help.png"><a href="navmap?helpmenu=active">Help</a></li>
</ul>
</div>
<div id="configure_window" style="display:none;">
	<div id="configure_tabs" class="nav"><ul><li id="colours_tab" class="active"><a href="#" onclick="$('configure_colours').show();$('configure_filters').hide();$('filters_tab').className='';$('colours_tab').className='active';">Map Colours</a></li><li id="filters_tab"><a href="#" onclick="$('configure_filters').show();$('configure_colours').hide();$('filters_tab').className='active';$('colours_tab').className='';">Filters</a></li></ul></div>
	<div>

	<div id="configure_colours">

		<select id="base_colour" onchange="setColours(this.value);">
			<option style="background-color:#B41A1A;color:#FFFFFF;" value="#B41A1A"<?cs if:args.base_colour=='red' ?> selected<?cs /if ?>>red</option>
			<option style="background-color:#003300;color:#FFFFFF;" value="#003300"<?cs if:args.base_colour=='green' ?> selected<?cs /if ?>>green</option>
			<option style="background-color:#000033;color:#FFFFFF;" value="#000033"<?cs if:args.base_colour=='blue' ?> selected<?cs /if ?>>blue</option>
			<option style="background-color:#000000;color:#FFFFFF;" value="#000000"<?cs if:args.base_colour=='black' ?> selected<?cs /if ?>>black</option>
			<option style="background-color:#330033;color:#FFFFFF;" value="#330033"<?cs if:args.base_colour=='purple' ?> selected<?cs /if ?>>purple</option>
			<option style="background-color:#333300;color:#FFFFFF;" value="#333300"<?cs if:args.base_colour=='yellow' ?> selected<?cs /if ?>>yellow</option>
			<option style="background-color:#003333;color:#FFFFFF;" value="#003333"<?cs if:args.base_colour=='aqua' ?> selected<?cs /if ?>>aqua</option>
		</select>
	<div id="colour_no"><?cs var:args.colour_no ?> Colours</div>
	<div id="colour_track" style="background-color:lightgrey;width:150px;height:8px;margin-bottom:10px;">
		<div id="colour_slider" style="background:url(<?cs var:chrome.href ?>/wikinavmap/images/slider.png);width:15px;height:18px;cursor:move;">
		</div>
	</div>
	<form id="colour_form">
	</form>
	<div style="font-size:10px">
	<a href="#" onclick="showDates()" id="showdates">show dates</a> |
	<a href="#" onclick="setDates(null);calculateTimes();">reset to defaults</a>
	</div>
	</div>
	<div id="configure_filters" style="display:none">
	<form id="filter_form">
	<label>Nodes to Display:</label>
	<div>
		<input type="checkbox" <?cs if:args.show_tickets ?>checked="checked"<?cs /if ?> name="show_tickets" id="show_tickets" onclick="if(this.checked){$('ticket_filter').enable();}else{$('ticket_filter').disable();$('t_username').disable();}" />Tickets<br/>
		<select id="ticket_filter" name="ticket_filter" onchange="if (this.value=='user' || this.value=='useractive'){ $('t_username').enable(); } else { $('t_username').disable(); }">
			<option value="all"<?cs if:args.ticket_filter=='all' ?> selected<?cs /if ?>>All Tickets (including closed)</option>
			<option value="active"<?cs if:args.ticket_filter=='active' ?> selected<?cs /if ?>>Active Tickets</option>
			<option value="mine"<?cs if:args.ticket_filter=='mine' ?> selected<?cs /if ?>>My Tickets (including closed)</option>
			<option value="myactive"<?cs if:(args.ticket_filter=='myactive' || !args.ticket_filter) ?> selected<?cs /if ?>>My Active Tickets</option>
			<option value="user"<?cs if:args.ticket_filter=='user' ?> selected<?cs /if ?>>Tickets belonging to ... (including closed)</option>
			<option value="useractive"<?cs if:args.ticket_filter=='useractive' ?> selected<?cs /if ?>>Active Tickets belonging to ...</option>
		</select>
	</div>
	Username: <select id="t_username" name="t_username"<?cs if:(args.ticket_filter!='user' && args.ticket_filter!='useractive') ?> disabled="true"<?cs /if ?>>
		<?cs each:user = users ?>
		<option value="<?cs var:user ?>"<?cs if:user==args.t_username ?> selected<?cs /if ?>><?cs var:user ?></option>
		<?cs /each ?>
	</select>
	<div>
		<input type="checkbox" <?cs if:args.show_wiki ?>checked="checked"<?cs /if ?> name="show_wiki" id="show_wiki" onclick="if(this.checked){$('wiki_filter').enable();}else{$('wiki_filter').disable();$('w_username').disable();}" />Wiki Pages <br/>
		<select id="wiki_filter" name="wiki_filter" onchange="if (this.value=='user'){ $('w_username').enable(); } else { $('w_username').disable(); }">
			<option value="all"<?cs if:args.wiki_filter=='all' ?> selected<?cs /if ?>>All Wiki Pages</option>
			<option value="mine"<?cs if:args.wiki_filter=='mine' ?> selected<?cs /if ?>>Wiki Pages edited by Me</option>
			<option value="others"<?cs if:args.wiki_filter=='others' ?> selected<?cs /if ?>>Wiki Pages NOT edited by Me</option>
			<option value="user"<?cs if:args.wiki_filter=='user' ?> selected<?cs /if ?>>Wiki Pages edited by ...</option>
		</select>
	</div>
	Username: <select id="w_username" name="w_username"<?cs if:(args.wiki_filter!='user') ?> disabled="true"<?cs /if ?>>
		<?cs each:user = users ?>
		<option value="<?cs var:user ?>"<?cs if:user==args.w_username ?> selected<?cs /if ?>><?cs var:user ?></option>
		<?cs /each ?>
	</select>
	</form>
	</div>
	<input type="submit" onclick="loadMapData('mapdata', '<?cs var:args.referer ?>', '<?cs var:chrome.href ?>/wikinavmap/images/loading.gif');" value="OK" />
	<input type="submit" onclick="hideModal('configure_window');" value="Cancel" />
	<div id="date_err">
	</div>
	</div>
</div>
<div id="content" class="wikinavmap">
<div id="top">
 <h1>WikiNavMap</h1> 
	<span id="filter_description" style="font-style:italic;"></span>
	<div id="colour_key_top">
		
	</div>
	<div id="searchBox">
		
	</div>
</div>
	<div id="mapdata">
	</div>
	

</div>
<script type="text/javascript">
setConfiguration();
<?cs if:args.colour_no ?>
slider.setValue(<?cs var:args.colour_no ?>)
<?cs else ?>
slider.setValue(<?cs var:wikinavmap.default_colour_no ?>)
<?cs /if ?>
setDates("<?cs var:args.date0 ?><?cs if:args.date1 ?>,<?cs var:args.date1 ?><?cs /if ?><?cs if:args.date2 ?>,<?cs var:args.date2 ?><?cs /if ?><?cs if:args.date3 ?>,<?cs var:args.date3 ?><?cs /if ?><?cs if:args.date4 ?>,<?cs var:args.date4 ?><?cs /if ?>");
loadMapData('mapdata', '<?cs var:args.referer ?>', '<?cs var:chrome.href ?>/wikinavmap/images/loading.gif');
window.onresize = setDimensions;
</script>

<?cs include "footer.cs"?>
