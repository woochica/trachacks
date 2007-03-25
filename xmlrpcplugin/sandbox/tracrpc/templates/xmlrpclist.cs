<?cs include "header.cs"?>
<?cs include "macros.cs"?>

<div id="ctxtnav" class="nav"></div>

<div id="content" class="wiki">

<div id="test">
Hello world
</div>

<h2>XML-RPC exported functions</h2>

<div id="searchable">
<dl>
<?cs each:namespace = xmlrpc.functions ?>

<dt><h3 id=xmlrpc.<?cs var:namespace.namespace ?>><?cs var:namespace.namespace ?> - <?cs var:namespace.description ?></h3></dt>
<dd>
<table class="listing tickets">
<thead>
<tr>
<th>Function</th>
<th>Description</th>
<th><nobr>Permission required</nobr></th>
</tr>
</thead>

<?cs set idx = #0 ?>
<tbody>
<?cs each:function = namespace.methods ?>
<tr class="<?cs if idx % #2 == 0 ?>even<?cs else ?>odd<?cs /if ?>" style="">
<td><div class="function"><?cs var:function.0?></div></td><td><?cs var:function.1?></td><td><?cs var:function.2 ?></td>
</tr>
<?cs set idx = idx + #1 ?>
<?cs /each ?>
</tbody>
</table>
</dd>
<?cs /each ?>
</dl>
</div>

<script type="text/javascript">//<![CDATA[
$.fn.addAnchor = function(title) {
  title = title || "Link here";
  return this.filter("*[@id]").each(function() {
    $("<a class='anchor'> \u00B6</a>").attr("href", "#" + this.id)
      .attr("title", title).appendTo(this);
  });
}

$(document).ready(function(){
  $("#content").find("h1,h2,h3,h4,h5,h6").addAnchor("Link to this section");

  rpc = new $.jsonrpc("http://localhost:8080/stable/jsonrpc");
  rpc.expose("wiki.getRPCVersionSupported");
  rpc.expose("wiki.getPage");
  rpc.expose("wiki.getAllPages");
  rpc.expose("wiki.getPageHTML");
  rpc.expose("search.performSearch");
  rpc.expose("ticket.status.getAll");

  $("#test").click(function() {
    //$("#content table tr.color3-even").contains("WIKI_VIEW").toggle();

    rpc.server.search.performSearch(function(hits) {
	  for (var i in hits) {
		$("#test").after(escape(hits[i][3]) + "<br>\n");
	  }
    }, "alec thomas");
  })
});
//]]>
</script>

</div>

<?cs include:"footer.cs"?>
