<!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
 <title>HighlightMacro: Highlight.py - Trac Hacks - Plugins Macros etc. - Trac</title><link rel="start" href="/wiki" /><link rel="search" href="/search" /><link rel="help" href="/wiki/TracGuide" /><link rel="stylesheet" href="/chrome/common/css/trac.css" type="text/css" /><link rel="stylesheet" href="/chrome/redirect/css/redirect.css" type="text/css" /><link rel="stylesheet" href="/chrome/common/css/code.css" type="text/css" /><link rel="stylesheet" href="/pygments/trac.css" /><link rel="icon" href="/favicon.ico" type="image/x-icon" /><link rel="shortcut icon" href="/favicon.ico" type="image/x-icon" /><link rel="up" href="/wiki/HighlightMacro" title="HighlightMacro" /><link rel="alternate" href="/attachment/wiki/HighlightMacro/Highlight.py?format=raw" title="Original Format" type="text/x-python; charset=iso-8859-15" /><style type="text/css">/* vim: syntax=css
*/
form, input, body {
	background-image: url(/chrome/site/trachacks_bg.png);
	background-position: 64px 64px;
}

#ticket form {
	background-image: none;
}

form#search {
	background: transparent;
}

pre, tt {
	color: #600;
}

.ext-link {
	background-image: none;
	padding-left: 0px;
	border-bottom: solid 1px;
}

/* For Mozilla and Safari */
*>#content {
	padding: 0;
	margin: 15px 15px 0 15px;
	text-align: left;
	min-height: 770px;
}

/* For IE */
* html #content {
	padding: 0;
	margin: 15px 15px 0 15px;
	text-align: left;
	height: 770px;
}

#newsflash {
	border: solid 2px #8f8;
	width: 400px;
	float: right;
	background: #dfd;
	font-size: 0.8em;
	margin: 0em;
	margin-left: 1em;
	padding: 0.5em 1em 0.5em 1em;
}

#newsflash h1 {
	font-size: 1.2em;
	padding: 0em;
	margin: 0em;
}

#newsflash .post hr {
	display: none;
}

span.tagcount {
	color: #999;
	font-size: 0.6em;
	vertical-align: middle;
}

#newticketguide {
 background: #fdc;
 border: 2px solid #d00;
 font-style: italic;
 padding: 0 .5em;
 margin: 1em 0;
 text-align: center;
}

#newticketguide h1 {
	font-variant: small-caps;
	letter-spacing: 0.3em;
	font-weight: bold;
}

#newticketguide hr {
	padding: 0;
	margin: 1em auto;
	width: 40%;
	text-align: center;
	border: 1px dotted #d00;
}
</style>
 <script type="text/javascript" src="/chrome/common/js/trac.js"></script>
</head>
<body>


<div id="banner">

<div id="header"><a id="logo" href="http://trac-hacks.org/"><img src="/chrome/site/trachacks_banner.png" width="300" height="73" alt="Trac Hacks" /></a><hr /></div>

<form id="search" action="/search" method="get">
 <div>
  <label for="proj-search">Search:</label>
  <input type="text" id="proj-search" name="q" size="10" accesskey="f" value="" />
  <input type="submit" value="Search" />
  <input type="hidden" name="wiki" value="on" />
  <input type="hidden" name="changeset" value="on" />
  <input type="hidden" name="ticket" value="on" />
 </div>
</form>



<div id="metanav" class="nav"><ul><li class="first">logged in as rjollos</li><li><a href="/logout">Logout</a></li><li><a href="/settings">Settings</a></li><li><a accesskey="6" href="/wiki/TracGuide">Help/Guide</a></li><li><a href="/about">About Trac</a></li><li class="last"><a href="/account">My Account</a></li></ul></div>
</div>

<div id="mainnav" class="nav"><ul><li class="active first"><a accesskey="1" href="/wiki">Wiki</a></li><li><a accesskey="2" href="/timeline">Timeline</a></li><li><a href="/browser">Browse Source</a></li><li><a href="/report">View Tickets</a></li><li><a accesskey="7" href="/newticket">New Ticket</a></li><li><a accesskey="4" href="/search">Search</a></li><li><a href="/tags" accesskey="T">Tags</a></li><li><a href="/admin">Admin</a></li><li class="last"><a href="/blog">Blog</a></li></ul></div>
<div id="main">




<div id="ctxtnav" class="nav"></div>

<div id="content" class="attachment">


 <h1><a href="/wiki/HighlightMacro">HighlightMacro</a>: Highlight.py</h1>
 <table id="info" summary="Description"><tbody><tr>
   <th scope="col">
    File Highlight.py, 286 bytes 
    (added by relaxdiego,  4 years ago)
   </th></tr><tr>
   <td class="message"></td>
  </tr>
 </tbody></table>
 <div id="preview">
   <table class="code"><thead><tr><th class="lineno">Line</th><th class="content">&nbsp;</th></tr></thead><tbody><tr><th id="L1"><a href="#L1">1</a></th>
<td><span class="kn">from</span>&nbsp;<span class="nn">StringIO</span> <span class="kn">import</span> <span class="n">StringIO</span></td>
</tr><tr><th id="L2"><a href="#L2">2</a></th>
<td><span class="kn">import</span>&nbsp;<span class="nn">re</span></td>
</tr><tr><th id="L3"><a href="#L3">3</a></th>
<td></td>
</tr><tr><th id="L4"><a href="#L4">4</a></th>
<td><span class="k">def</span>&nbsp;<span class="nf">execute</span><span class="p">(</span><span class="n">hdf</span><span class="p">,</span> <span class="n">args</span><span class="p">,</span> <span class="n">env</span><span class="p">):</span></td>
</tr><tr><th id="L5"><a href="#L5">5</a></th>
<td>&nbsp; &nbsp; <span class="n">arguments</span> <span class="o">=</span> <span class="n">re</span><span class="o">.</span><span class="n">split</span><span class="p">(</span><span class="s">&#39;\s*,\s*&#39;</span><span class="p">,</span> <span class="n">args</span><span class="p">)</span></td>
</tr><tr><th id="L6"><a href="#L6">6</a></th>
<td></td>
</tr><tr><th id="L7"><a href="#L7">7</a></th>
<td>&nbsp; &nbsp; <span class="n">buf</span> <span class="o">=</span> <span class="n">StringIO</span><span class="p">()</span></td>
</tr><tr><th id="L8"><a href="#L8">8</a></th>
<td></td>
</tr><tr><th id="L9"><a href="#L9">9</a></th>
<td>&nbsp; &nbsp; <span class="n">buf</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="s">&#39;&lt;span style=&quot;background-color:#</span><span class="si">%s</span><span class="s">&quot;&gt;&#39;</span> <span class="o">%</span> <span class="n">arguments</span><span class="p">[</span><span class="mi">0</span><span class="p">])</span></td>
</tr><tr><th id="L10"><a href="#L10">10</a></th>
<td>&nbsp; &nbsp; <span class="n">buf</span><span class="o">.</span><span class="n">write</span><span class="p">(</span><span class="s">&#39;</span><span class="si">%s</span><span class="s">&lt;/span&gt;&#39;</span> <span class="o">%</span> <span class="n">arguments</span><span class="p">[</span><span class="mi">1</span><span class="p">])</span></td>
</tr><tr><th id="L11"><a href="#L11">11</a></th>
<td></td>
</tr><tr><th id="L12"><a href="#L12">12</a></th>
<td>&nbsp; &nbsp; <span class="k">return</span> <span class="n">buf</span><span class="o">.</span><span class="n">getvalue</span><span class="p">()</span></td>
</tr></tbody></table>
 </div>
 <div class="buttons">
  <form method="get" action=""><div id="delete">
   <input type="hidden" name="action" value="delete" />
   <input type="submit" value="Delete attachment" />
  </div></form>
 </div>


</div>
<script type="text/javascript">searchHighlight()</script>
<div id="altlinks"><h3>Download in other formats:</h3><ul><li class="first last"><a href="/attachment/wiki/HighlightMacro/Highlight.py?format=raw">Original Format</a></li></ul></div>

</div>

<div id="footer">
 <hr />
 <a id="tracpowered" href="http://trac.edgewall.org/"><img src="/chrome/common/trac_logo_mini.png" height="30" width="107"
   alt="Trac Powered"/></a>
 <p class="left">
  Powered by <a href="/about"><strong>Trac 0.10.6dev</strong></a><br />
  By <a href="http://www.edgewall.org/">Edgewall Software</a>.
 </p>
 <p class="right">
  Hosting sponsored by <a href="http://www.tgc.de" style="border-bottom: 0;"><img src="/chrome/site/tgc-logo-30x210.png" alt="true global communications GmbH" /></a>
 </p>
</div>



 </body>
</html>

