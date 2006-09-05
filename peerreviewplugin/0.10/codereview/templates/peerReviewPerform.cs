<?cs include "header.cs" ?>
<?cs include "macros.cs" ?>

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

<br>
<b>File Information</b>
<br>

<table border="0" width="100%" style="border-collapse: collapse" id="infoTable">
    <tr>
        <td>
            Path: <?cs var:review.path ?>
        </td>
    </tr>
    <tr>
        <td>
            Revision: <?cs var:review.version ?>
        </td>
    </tr>
    <tr>
        <td>
            Start Line: <?cs var:review.lineStart ?><br>
    </tr>
    <tr>
    	<td>
            End Line: <?cs var:review.lineEnd ?><br>
        </td>
    </tr>
</table>
<br>

<table border="0" width="100%" style="border-collapse: collapse" id="table1">
    <tr>
        <td align="left"><font size="2">Click line number to Add/View comments</font></td>
        <td align="right"><font size="2">View <input type="text" id="SelectRangeTextBox" size="1" value="3"
	onKeyDown="if(event.keyCode == 13 || event.keyCode == 3){resetLines();}" style="text-align: center"> lines on either side of selection.</font>
        </td>
    </tr>
</table>

<!-- displays the contents of the file being reviewed -->
<div id="FilePreview">
<?cs var:file.preview ?>
</div>

<br>
Back to the<a href="<?cs var:trac.href.peerReviewView ?>?Review=<?cs var:review.reviewID ?>"> Code Review Details</a> page
<br><br>

<div id="ViewCommentArea" style="position:absolute;left:0px;top:0px;z-index:1;display:none;width:455px;height:500px;" cellpadding="0" cellspacing="0">
<table width="450px" bgcolor="#F7F7F7" style="border-collapse: collapse;">
  <tr height="15px">
    <td id="ViewCommentTitle" width="432px" onmousedown="dragStart(event, 'ViewCommentArea');" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/top_bar_repeater_1x17.gif">
    </td>
    <td width="18px" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/close_btn_18x17.gif" onclick="closeCommentWindow('ViewCommentArea');"></td>
  </tr>
  <tr height="10px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td width="450px" align="center" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2">
      <div style="background-color: #F7F7F7; border: 1px solid #C0C0C0; overflow: auto; max-height: 400px; width: 425px" id="innerCommentDiv">
	Loading...
      </div>
    </td>
  </tr>
  <tr height="5px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td width="450px" align="right" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2" id="ViewAddCommentButtonArea">      
    </td>
  </tr>
  <tr height="3px">
    <td style="border-left: 1px solid #C8C8C8; border-bottom: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
</table>
</div>

<div id="AddCommentArea" style="position:absolute;left:0px;top:0px;z-index:1;display:none;width:305px;height:325px;">
<table width="300px" bgcolor="#F7F7F7" style="border-collapse: collapse;">
  <tr height="15px">
    <td id="AddCommentTitleArea" width="282px" onmousedown="dragStart(event, 'AddCommentArea');" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/top_bar_repeater_1x17.gif">
    </td>
    <td width="18px" style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000;" background="<?cs var:chrome.href ?>/hw/images/close_btn_18x17.gif" onclick="closeCommentWindow('AddCommentArea');"></td>
  </tr>
  <tr height="10px">
    <td style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
  <tr>
    <td valign="top" style="border-left: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2">
	<iframe frameborder="0" name="internalAddComment" id="internalAddComment" marginHeight="0" marginWidth="0" style="width:285px; height:196px" src="<?cs var:trac.href.peerReviewCommentCallback ?>"></iframe>
    </td>
  </tr>
  <tr height="2px">
    <td style="border-left: 1px solid #C8C8C8; border-bottom: 1px solid #C8C8C8; border-right: 1px solid #C8C8C8;" colspan="2"></td>
  </tr>
</table>

</div>

<script type="text/javascript">
<!--

var GLOBAL_fileID = -1;
var GLOBAL_lineNum = -1;
var GLOBAL_parentID = -1;
var GLOBAL_gettingComment = false;
var GLOBAL_yPosAdd = 0;
var GLOBAL_yPosView = 0;

function DOMWindowGetInnerWidth() {
    if (self.innerWidth)
        return self.innerWidth;
    else if(document.documentElement && document.documentElement.clientWidth)
        return document.documentElement.clientWidth;
    else if(document.body)
        return document.body.clientWidth;
}

function DOMWindowGetInnerHeight() {
   if (self.innerHeight)
        return self.innerHeight;
    else if(document.documentElement && document.documentElement.clientHeight)
        return document.documentElement.clientHeight;
    else if(document.body)
        return document.body.clientHeight;
}

function DOMWindowGetYOffset() {
    if (self.pageYOffset)
	    return self.pageYOffset;
    else if (document.documentElement && document.documentElement.scrollTop)
	    return document.documentElement.scrollTop;
    else if (document.body)
        return document.body.scrollTop;
}

function hideLines()
{
    var i = 1;
    var row = null;
    while((row = document.getElementById('L' + i)) != null)
    {
        if((i >= (lineStart - lineRange)) && (i <= (lineEnd + lineRange)))
        {
            (row.parentNode).style.display = '';
        }
        else
        {
            (row.parentNode).style.display = 'none';
        }
        i++;
    }
}

function init()
{
    var area = document.getElementById('ViewCommentArea');
    area.style.left = ((DOMWindowGetInnerWidth() / 2) - 225) + "px";
    GLOBAL_yPosView = ((DOMWindowGetInnerHeight() /2) - 100);
    area.style.top = GLOBAL_yPosView + "px";
    area = document.getElementById('AddCommentArea');
    area.style.left = ((DOMWindowGetInnerWidth() / 2) - 150) + "px";
    GLOBAL_yPosAdd = ((DOMWindowGetInnerHeight() /2) - 150);
    area.style.top = GLOBAL_yPosAdd + "px";
}

function resetLines()
{
    var textBox = document.getElementById('SelectRangeTextBox');
    var range = parseInt(textBox.value);
    if(isNaN(range))
    {
        textBox.value = lineRange;
        return;
    }
    if(range < 0)
    {
 	range = 0;
    }
    lineRange = range;
    hideLines();
    textBox.value = lineRange;
    return;
}

function createXMLObject(){
    var xmlObj = null;
    if(window.XMLHttpRequest){
        xmlObj = new XMLHttpRequest();
    } else if(window.ActiveXObject){
        xmlObj = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlObj;
}

function commentCallback(url){
    var xmlObj = createXMLObject();
    if(xmlObj != null){
        xmlObj.onreadystatechange = function(){
            if(xmlObj.readyState == 4){
                placeComment(xmlObj.responseText);
            }
        }
        xmlObj.open ('GET', url, true);
        xmlObj.send ('');
    }
    lastPick = null;
}

function placeComment(html)
{
    var area = document.getElementById('innerCommentDiv');
    area.innerHTML = html;

    resetInnerDivSize();
}

function resetInnerDivSize()
{
    var innerDiv = document.getElementById('innerCommentDiv');
    innerDiv.style.height = "";

    if(innerDiv.clientHeight >= 400)
    {
        innerDiv.style.height = 400;
    }
    else
    {
	innerDiv.style.height = (innerDiv.clientHeight + 5) + "px";
    }

    innerDiv = document.getElementById('ViewCommentArea');
    innerDiv.style.height = "";
    innerDiv.style.height = (innerDiv.clientHeight + 5) + "px";
}

function collapseComments(parentID)
{
    var area = document.getElementById('innerCommentDiv');
    for(var i =0; i<area.childNodes.length; i++)
        {
            if(area.childNodes[i].id != null)
		{
		    var ids = area.childNodes[i].id.split(':');
		    if(ids.length == 2 && ids[0] == parentID)
			{
			    area.childNodes[i].style.display = "none";
			    collapseComments(ids[1]);
			}
		}
	}
    
    var imgCell = document.getElementById(parentID + 'TreeButton');
    if(imgCell.innerHTML != "")
	imgCell.innerHTML = "<img src=\"" + plusUrl + "\" onclick=\"expandComments('" + parentID + "')\">";

    resetInnerDivSize();
}

function expandComments(parentID)
{
    var area = document.getElementById('innerCommentDiv');
    for(var i =0; i<area.childNodes.length; i++)
        {
            if(area.childNodes[i].id != null)
		{
		    var ids = area.childNodes[i].id.split(':');
		    if(ids.length == 2 && ids[0] == parentID)
			{
			    area.childNodes[i].style.display = "";
			}
		}
	}
    
    var imgCell = document.getElementById(parentID + 'TreeButton');
    if(imgCell.innerHTML != "")
	imgCell.innerHTML = "<img src=\"" + minusUrl + "\" onclick=\"collapseComments('" + parentID + "')\">";

    resetInnerDivSize();
}

function getComments(LineNum, fileID)
{
    getCommentsFull(LineNum, fileID, false);
}

function getCommentsFull(LineNum, fileID, wait)
{
    var area = document.getElementById('innerCommentDiv');
    area.innerHTML = "Loading...";
    area = document.getElementById('ViewCommentArea');
    area.style.display = "";
    var offset = DOMWindowGetYOffset();
    if(GLOBAL_yPosView < 0)
        GLOBAL_yPosView = 0;
    area.style.top = (offset + GLOBAL_yPosView) + "px";
    resetInnerDivSize();

    area = document.getElementById('ViewCommentTitle');
    area.innerHTML = "<table cellpadding=\"0\" cellspacing=\"0\" style=\"border-collapse: collapse;\" width=\"100%\"><tr><td align=\"left\">Comments On Line " + LineNum + "</td><td align=\"right\" valign=\"middle\"><a href=\"javascript:getComments(" + LineNum + "," + fileID + ")\"><font size=\"1\">Refresh</font></a>&nbsp;</td></tr></table>";

    area = document.getElementById('ViewAddCommentButtonArea');
    area.innerHTML = "<input type=button value=\"Add New Comment\" style=\"font-size: 10;\" onclick=\"addComment('" + LineNum + "', '" + fileID + "', '-1');\">&nbsp;&nbsp;";

    if(!wait)
	getCommentsPart2(LineNum, fileID);

}

function getCommentsPart2(LineNum, fileID)
{
    commentCallback(baseUrl + '?actionType=getCommentTree&IDFile=' + fileID + '&LineNum=' + LineNum);
}

function addComment(LineNum, fileID, parentID)
{
    var area = document.getElementById('AddCommentArea');
    var titlePlace = document.getElementById('AddCommentTitleArea');
    if(parentID < 0)
    {
	titlePlace.innerHTML = "Add Comment For Line " + LineNum;
    }
    else
    {
	titlePlace.innerHTML = "Reply To Comment On Line " + LineNum;
    }

    GLOBAL_fileID = fileID;
    GLOBAL_parentID = parentID;
    GLOBAL_LineNum = LineNum;

    var offset = DOMWindowGetYOffset();
    if(GLOBAL_yPosAdd < 0)
        GLOBAL_yPosAdd = 0;
    area.style.top = (offset + GLOBAL_yPosAdd) + "px";

    area.style.display = "";
    area.style.zIndex = ++dragObj.zIndex;
    
    if(window.frames['internalAddComment'])
    {
	    var iDoc = window.frames['internalAddComment'].document;
	    var button = iDoc.getElementById('AddCommentButtonArea');
	    if(button != null)
	    {
    		button.innerHTML = "<input style=\"font-size: 10;\" type=button onclick=\"submitComment(" + LineNum + ", " + fileID + ", " +  parentID + ")\" value=\"Add Comment\">&nbsp;&nbsp;";
        	GLOBAL_fileID = -1;
	        GLOBAL_LineNum = -1;
		window.setTimeout('resetAddCommentBoxSize()', 5);
	    }
    }
}

function resetAddCommentBoxSize()
{
	if(window.frames['internalAddComment'])
    	{
        	var iDoc = window.frames['internalAddComment'].document;
        	var acT = iDoc.getElementById('addCommentTable');
		var iFr = document.getElementById('internalAddComment');
		iFr.style.height = "";
		iFr.style.height = (acT.clientHeight + 15) + "px";
	}

	innerDiv = document.getElementById('AddCommentArea');
	innerDiv.style.height = "";
	innerDiv.style.height = (innerDiv.clientHeight + 3) + "px";
}

function submitComment(LineNum, fileID, parentID)
{
    var area = document.getElementById('L' + LineNum);
    area.innerHTML = "<a href=\"javascript:getComments(" + LineNum + ", " + fileID + ")\"><img src=\"" + tacUrl + "\">&nbsp;" + LineNum + "</a>";
    
    GLOBAL_fileID = fileID;
    GLOBAL_LineNum = LineNum;
    GLOBAL_gettingComment = true;

    getCommentsFull(LineNum, fileID, true); 
}

function timeToHide(line, fileID, parentID)
{
    area = document.getElementById('AddCommentArea');
    area.style.top = "-10000px"

    if(line != -1)
    	submitComment(line, fileID, parentID);
}

function timeToGetTree()
{
    area = document.getElementById('AddCommentArea');
    
    if(GLOBAL_fileID != -1 && GLOBAL_LineNum != -1 && GLOBAL_gettingComment)
    {
	area.style.display = "none";
	window.setTimeout('getCommentsPart2('+GLOBAL_LineNum+', '+GLOBAL_fileID+')', 5); 
        GLOBAL_fileID = -1;
        GLOBAL_LineNum = -1;
        GLOBAL_gettingComment = false;
    }
    else if(GLOBAL_fileID != -1 && GLOBAL_LineNum != -1)
    {
	var iDoc = window.frames['internalAddComment'].document;
	var button = iDoc.getElementById('AddCommentButtonArea');
	button.innerHTML = "<input style=\"font-size: 10;\" type=button onclick=\"submitComment(" + GLOBAL_LineNum + ", " + GLOBAL_fileID + ", " +  GLOBAL_parentID + ")\" value=\"Add Comment\">&nbsp;&nbsp;";
	GLOBAL_fileID = -1;
        GLOBAL_LineNum = -1;
	resetAddCommentBoxSize();
    }
    else
    {
	area.style.display = "none";
    }
}

function closeCommentWindow(area)
{
	var area = document.getElementById(area);
	area.style.display = "none";
}

function Browser() {

    var ua, s, i;

    this.isIE    = false;
    this.isNS    = false;
    this.version = null;

    ua = navigator.userAgent;

    s = "MSIE";
    if ((i = ua.indexOf(s)) >= 0) {
	this.isIE = true;
	this.version = parseFloat(ua.substr(i + s.length));
	return;
    }

    s = "Netscape6/";
    if ((i = ua.indexOf(s)) >= 0) {
	this.isNS = true;
	this.version = parseFloat(ua.substr(i + s.length));
	return;
    }

    // Treat any other "Gecko" browser as NS 6.1.

    s = "Gecko";
    if ((i = ua.indexOf(s)) >= 0) {
	this.isNS = true;
	this.version = 6.1;
	return;
    }
}

function dragStart(event, id) 
{

    var el;
    var x, y;

    // If an element id was given, find it. Otherwise use the element being
    // clicked on.

    if (id)
	{
	dragObj.elNode = document.getElementById(id);
	}
    else 
	{
	    if (browser.isIE)
		dragObj.elNode = window.event.srcElement;
	    if (browser.isNS)
		dragObj.elNode = event.target;

	    // If this is a text node, use its parent element.
	    
	    if (dragObj.elNode.nodeType == 3)
		dragObj.elNode = dragObj.elNode.parentNode;
	}

    if (browser.isIE) {
    x = window.event.clientX + document.documentElement.scrollLeft
	+ document.body.scrollLeft;
    y = window.event.clientY + document.documentElement.scrollTop
	+ document.body.scrollTop;
    }
    if (browser.isNS) {
	x = event.clientX + window.scrollX;
	y = event.clientY + window.scrollY;
    }

    dragObj.cursorStartX = x;
    dragObj.cursorStartY = y;
    dragObj.elStartLeft  = parseInt(dragObj.elNode.style.left, 10);
    dragObj.elStartTop   = parseInt(dragObj.elNode.style.top,  10);

    if (isNaN(dragObj.elStartLeft)) dragObj.elStartLeft = 0;
    if (isNaN(dragObj.elStartTop))  dragObj.elStartTop  = 0;
    if(id != 'ViewCommentArea')
    {
        dragObj.elNode.style.zIndex = ++dragObj.zIndex;
    }

    if (browser.isIE) {
	document.attachEvent("onmousemove", dragGo);
	document.attachEvent("onmouseup",   dragStop);
	window.event.cancelBubble = true;
	window.event.returnValue = false;
    }
    if (browser.isNS) {
	document.addEventListener("mousemove", dragGo,   true);
	document.addEventListener("mouseup",   dragStop, true);
	event.preventDefault();
    }

}

function dragGo(event) {

    var x, y;

    // Get cursor position with respect to the page.

    if (browser.isIE) {
    x = window.event.clientX + document.documentElement.scrollLeft
	+ document.body.scrollLeft;
    y = window.event.clientY + document.documentElement.scrollTop
	+ document.body.scrollTop;
    }
    if (browser.isNS) {
	x = event.clientX + window.scrollX;
	y = event.clientY + window.scrollY;
    }

  dragObj.elNode.style.left =
      (dragObj.elStartLeft + x - dragObj.cursorStartX) + "px";
  dragObj.elNode.style.top  =
      (dragObj.elStartTop  + y - dragObj.cursorStartY) + "px";

  if (browser.isIE) {
      window.event.cancelBubble = true;
      window.event.returnValue = false;
  }
  if (browser.isNS)
      event.preventDefault();

}

function dragStop(event) {

    // Stop capturing mousemove and mouseup events.

    if (browser.isIE) {
	document.detachEvent("onmousemove", dragGo);
	document.detachEvent("onmouseup",   dragStop);
    }
    if (browser.isNS) {
	document.removeEventListener("mousemove", dragGo,   true);
	document.removeEventListener("mouseup",   dragStop, true);
    }

    var val = parseInt(dragObj.elNode.style.top) - DOMWindowGetYOffset();
    if(dragObj.elNode.id == 'ViewCommentArea')
        GLOBAL_yPosView = val;
    else
        GLOBAL_yPosAdd = val;
}

var baseUrl = "<?cs var:trac.href.peerReviewCommentCallback ?>";
var tacUrl = "<?cs var:trac.htdocs.thumbtac ?>";
var plusUrl = "<?cs var:trac.htdocs.plus ?>";
var minusUrl = "<?cs var:trac.htdocs.minus ?>";
var lineStart = <?cs var:review.lineStart ?>;
var lineEnd = <?cs var:review.lineEnd ?>;
var dragObj = new Object();
dragObj.zIndex = 0;
var browser = new Browser();
var lineRange = 3;
hideLines();
init();


//-->
</script>

<style>
<!--
table.code th.performCodeReview {
        width: 4em;
}
//-->
</style>

<?cs include "footer.cs" ?>
