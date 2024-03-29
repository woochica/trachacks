<?cs include:"header.cs"?>
<script type="text/javascript">
addEvent(window, 'load', function() { document.getElementById('q').focus()}); 
</script>
<div id="ctxtnav" class="nav"><?cs
 with:links = chrome.links ?><?cs
  if:len(links.prev) || len(links.next) ?><ul><?cs
   if:len(links.prev) ?>
    <li class="first<?cs if:!len(links.up) && !len(links.next) ?> last<?cs /if ?>">
     &larr; <a href="<?cs var:links.prev.0.href ?>"><?cs
       var:links.prev.0.title ?></a>
    </li><?cs
   /if ?><?cs
   if:len(links.next) ?>
    <li class="<?cs if:!len(links.prev) && !len(links.up) ?>first <?cs /if ?>last">
     <a href="<?cs var:links.next.0.href ?>"><?cs
       var:links.next.0.title ?></a> &rarr;
    </li><?cs
   /if ?></ul><?cs
  /if ?><?cs
 /with ?>
</div>

<div id="content" class="search">

<h1><label for="q">Szukaj</label></h1>
<form action="<?cs var:trac.href.search ?>" method="get">
 <p>
  <input type="text" id="q" name="q" size="40" value="<?cs var:search.q ?>" />
  <input type="submit" value="Szukaj" />
 </p>
 <p><?cs
  each filter=search.filters ?>
   <input type="checkbox" id="<?cs var:filter.name?>" 
          name="<?cs var:filter.name?>" <?cs
     if:filter.active ?>checked="checked"<?cs /if ?> />
   <label for="<?cs var:filter.name ?>"><?cs var:filter.label?></label><?cs
  /each ?>
 </p>
</form>
<?cs if:len(search.result) ?>
 <hr />
 <h2>Wyniki wyszukiwania <?cs
  if:search.n_pages > 1 ?>(<?cs
   var:(search.page-1) * search.page_size + 1 ?> - <?cs
   var:(search.page-1) * search.page_size + len(search.result) ?> 
   of <?cs var:search.n_hits?>)<?cs
  /if ?></h2>
 <div id="searchable">
  <dl id="results"><?cs
   each item=search.result ?>
 <dt><a href="<?cs var:item.href ?>"><?cs var:item.title ?></a></dt>
 <dd><?cs var:item.excerpt ?></dd>
 <dd>
  <span class="author">Wed�ug <?cs var:item.author ?></span> &mdash;
  <span class="date"><?cs var:item.date ?></span><?cs
  if:item.keywords ?> &mdash
   <span class="keywords">S�owa kluczowe: <em><?cs var:item.keywords ?></em></span><?cs
  /if ?>
 </dd><?cs
   /each ?>
  </dl>
  <hr />
 </div><?cs 
 if search.n_pages > 1 ?>
  <div id="paging"><?cs
  if len(chrome.links.prev) ?>
    <a href="<?cs var:chrome.links.prev.0.href ?>" title="<?cs
       var:chrome.links.prev.0.title ?>">&larr;</a> <?cs
  /if ?><?cs
  loop:p = 1, search.n_pages ?><?cs
    if p == search.page ?><?cs var:p ?><?cs
    else ?><a href="<?cs var:search.page_href + "&amp;page=" + p?>"><?cs
     var:p ?></a><?cs
    /if ?> <?cs
  /loop ?><?cs
  if len(chrome.links.next) ?>
    <a href="<?cs var:chrome.links.next.0.href ?>" title="<?cs
       var:chrome.links.next.0.title ?>">&rarr;</a><?cs
  /if ?>
  </div><?cs
 /if ?><?cs

elif:search.q ?>
 <div id="notfound">Nic nie znaleziono.</div><?cs
/if ?>

<div id="help">
 <strong>Pomoc:</strong> Zobacz <a href="<?cs
   var:trac.href.wiki ?>/TracSearch">TracSearch</a>, aby nauczy� si� lepiej wyszukiwa�.
</div>

</div>
<?cs include:"footer.cs"?>
