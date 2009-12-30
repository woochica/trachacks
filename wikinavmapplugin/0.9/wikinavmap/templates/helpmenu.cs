<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="content" class="wiki">

 
  
  
   
   <div class="wikipage">
    <div id="searchable"><p>
<div class='wiki-toc'>
<h4>Table of Contents</h4>
<ol><li class="active"><a href="#About">About</a></li><li class="active"><a href="#Troubleshooting">Troubleshooting</a></li><li class="active">
<a href="#Appearance">Appearance</a><ol><li class="active"><a href="#WikiPages">Wiki Pages</a></li><li class="active">
<a href="#TicketsMilestones">Tickets &amp; Milestones</a></li><li class="active">
<a href="#NodeProperties">Node Properties</a></li></ol><li class="active"><a href="#Navigation">Navigation</a><ol><li class="active"><a href="#ClickandDrag">Click and Drag</a></li><li class="active">

<a href="#GoTo">Go To</a></li><li class="active">
<a href="#Overview">Overview</a></li></ol><li class="active"><a href="#Configure">Configure</a><ol><li class="active"><a href="#MapColours">Map Colours</a></li><li class="active">
<a href="#Filters">Filters</a></li><li class="active">
<a href="#LinktothisPage">Link to this page</a></li></ol></li></ol></li></ol></div>

</p>
<h1>WikiNavMap Help</h2>
	
<h2 id="About">About</h2>
<p>
WikiNavMap visualises the Tickets, Wiki Pages and Milestones in the Trac environment. You can configure the appearance and what will be displayed by using the configuration interface. WikiNavMap aims to be a quick way for you to get both an overall picture of what is happening in the Trac environment and specific information about what individual users have been working on.

</p>
<p>
WikiNavMap is a Masters project by Adam Ullman, a student at the University of Sydney, School of Information Technologies. 
</p>
<h2 id="Troubleshooting">Troubleshooting</h2>
<p>
WikiNavMap has been tested on IE 7, Firefox 2 and Safari 2. If you are not using one of these browsers then you may not be experiencing WikiNavMap as it is intended. Try downloading Firefox from <a href="http://www.mozilla.com">http://www.mozilla.com</a>.
</p>
<p>
If you are using one of the above browsers and you are still having trouble loading the maps, or if the overview image isn't appearing correctly then try refreshing the WikiNavMap. The best way to do this without losing your settings is to click on the Link to this Page link.
</p>
<p>
If you are having any other problems with WikiNavMap please contact Adam Ullman at <a href="mailto:adam@it.usyd.edu.au">adam@it.usyd.edu.au</a> and describe the error that you are getting.
</p>
<h2 id="Appearance">Appearance</h2>
<p>
The WikiNavMap appears as a directed graph, with each node representing either a wiki page or a ticket and each grey arrow representing the hyperlinks between these nodes. Wiki pages are all grouped together within a grey border and tickets are grouped within a red border representing milestones.
</p>
<h3 id="WikiPages">Wiki Pages</h3>
<p>

Wiki pages appear as a square box with the title of the page inside it. 
</p>
<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Wiki-Pages.png" /></a>
</p>
<h3 id="TicketsMilestones">Tickets &amp; Milestones</h3>
<ul><li>Tickets appear as a box with the Ticket number on the left and the username of the person who has been assigned the ticket on the right. If the ticket has been completed then it will be bordered in red, otherwise it will be bordered in white. 
</li><li>Milestones appear as a red border around tickets. If the milestone has been completed it will have a grey background.
</li></ul><p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Completed-Ticket.png" /><br/>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Completed-Milestone.png" />
</p>
<h3 id="NodeProperties">Node Properties</h3>

<p>
Nodes are one of Wiki pages, Tickets or Milestones. Nodes have certain properties:
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Colour-Key.png" style="float:right" />
</p>
<ul><li><strong>Colour</strong> -- The colour of the wiki pages and tickets indicates the time at which it was last edited within the given date range, according to the colour key. This colour key can be customised by using the Configure interface. 
</li><li><strong>Font Size</strong> -- The font size of the text inside the tickets and wiki pages indicate the number of times they have been edited within the given date range. The larger the font size, the more times the wiki page or ticket has been edited, or commented on.
</li><li><strong>Links</strong> -- Every node in the WikiNavMap including milestones is a link to the respective page in Trac. So for example clicking on the WikiStart node in the map will bring you to the WikiStart page in the Trac wiki.

</li><img src="<?cs var:chrome.href ?>/wikinavmap/images/Popup.png" style="float:right" /><li><strong>Popups</strong> -- Hovering over nodes will bring up a popup that displays more information about a node. This information varies depending on the type of node. 
</li></ul><h2 id="Navigation">Navigation</h2>
<p>
There are three different ways to navigate around the WikiNavMap. 
</p>
<h3 id="ClickandDrag">Click and Drag</h3>
<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Drag.png" />
Clicking and dragging on the map scrolls the map around. This is similar to what you would find in applications such as Adobe Acrobat Reader and Google Maps.
</p>
<h3 id="GoTo">Go To</h3>

<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/GoTo.png" style="float:right" />
If you know what node you are looking for you can scroll straight to it by selecting it from the Go To pull down menu and pressing the Go To button. You will be immediately scrolled to the position of the node and a popup will appear displaying more information. If you click on the WikiNavMap link from a node (Wiki page, ticket or milestone) that is in the Go To list then this node will be selected when you first load the map.
</p>
<h3 id="Overview">Overview</h3>
<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Overview-Image.png" style="float:right" />
The overview map in the top right hand corner also allows you to navigate around the map. The overview map shows you a smaller version of the whole map, the blue square indicates the part of the map that is currently visible in the larger window. Dragging this blue square around to different positions on the overview will move you to this location on the larger map.

If you find that the overview appears to be squished or not appearing correctly you may need to refresh the page, the best way to do this is to click on Link to this page. This seems to happen particularly with Internet Explorer.
</p>
<p>
If the overview gets in the way you can hide it by clicking on <img src="<?cs var:chrome.href ?>/wikinavmap/images/Hide-Overview.png" /> in the top right hand corner. Clicking on this a second time will reveal the overview.

</p>
<h2 id="Configure">Configure</h2>
<p>
The real power of WikiNavMap lies in the ability to customise what is visualised by using the configuration interface. To access the configuration interface you click on <img src="<?cs var:chrome.href ?>/wikinavmap/images/Configure-Link.png" /> in the top right hand corner of the page. Once inside the configuration interface there are two separate Tabs which allow you to customise different elements of the map.
</p>
<h3 id="MapColours">Map Colours</h3>
<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Configure-Colours.png" />
</p>
<p>

This menu allows you to select the colours that will be used in the map and what time ranges those colours represent.
</p>
<ul><li>The first pull down menu allows you to select the base colour for the nodes. This is the first colour in a colour gradient that is automatically generated. 
</li><li>The number of colours in the gradient can be selected using the slide bar. 
</li><li>Each colour gradient represents a date range. There is a default date range which goes back in time from the current date however you can set the date range to be whatever you want. Clicking on the "show dates" link will reveal the date input boxes. Dates in these boxes must be going back in time starting from left to right and entered in the format DD/MM/YYYY. So the farthest left is the most recent and the farthest right is the oldest. 
</li></ul><h3 id="Filters">Filters</h3>
<p>
<img src="<?cs var:chrome.href ?>/wikinavmap/images/Configure-Filters.png" />
</p>
<p>
The filters menu allows you to specify which Tickets and Wiki Pages will be displayed. 
</p>
<ul><li>You can choose whether to display Tickets and Wiki Pages by checking or unchecking the checkboxes.
</li><li>You can select which Tickets and wiki pages to display from the pull down menu. If you choose an option that has a ... (missing username) in it then you can specify a user using the Username input field. 
</li></ul><h3 id="LinktothisPage">Link to this page</h3>

<p>
Once you have made changes to the configuration of the WikiNavMap, the URL in your address bar will no longer be valid. If you want to email the link to a WikiNavMap that you have configured or add it to a Wiki Page then you will need to: 
</p>
<ol><li>Right click on <img src="<?cs var:chrome.href ?>/wikinavmap/images/Link-to-this-Page.png" />
</li><li>Select Copy Link.
</li><li>Paste the link into the location of your choice
</li></ol>
Clicking on the Link to this page link is also a good way to refresh the page without losing your settings.

</div>


<?cs include "footer.cs"?>
