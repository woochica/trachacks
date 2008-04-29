<html>
<head>
    <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
    <title>Trac act~RelationTickets Query(%(myVer)s)</title>
<link rel="stylesheet" type="text/css" charset="utf-8" media="all" 
    href="ykstate.css">

</head>
<body topmargin="5" leftmargin="5" rightmargin="0" marginwidth="5" marginheight="5">



by:<sub>%(myVer)s </sub>
at:<sup> %(creaTime)s generated</sup>
<sub>
<a href="http://trac.rdev.kingsoft.net/kspeg/ticket/213">abt.Ticket</a>
</sub>
<h4>%(projname)s 项目传票关联状态报表::
</h4>

<img src="%(optproj)s-burndown.png">

<table id="relaTickets" >
<tr><td style="vertical-align: top">
<table id="relaTickets">
<tr>
<th>New</th>
<th>Doing</th>
<th>Done</th>
</tr>
    %(relatickets)s
<tr>
<th>.</th>
<td style="vertical-align: bottom;text-align: center">
    <br/><b><i>Summary</b></i>
    </td>
<th>.</th>
</tr>
<tr>
<th>New</th>
<th>Doing</th>
<th>Done</th>
</tr>
<tr>
<td>
    <ul>
    %(purenew)s
    </ul>
</td>
<td>
    <ul>
    %(puredoing)s
    </ul>
</td>
<td>
    <ul>
    %(puredone)s
    </ul>
</td>
</tr>
</table>
</td>
<td><!--Chat;Unplanned tickets:-->
<h5>unPlan</h5>
<br/>
    <ul>
    %(unplan)s
    </ul>

</td>
</tr>
</table>



</body>
</html>
