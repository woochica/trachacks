<?xml version="1.0"?>
<rss version="2.0">
 <channel><?cs
  if:project.name_encoded ?>
   <title><?cs var:project.name_encoded ?>: <?cs var:title ?></title><?cs
  else ?>
   <title><?cs var:title ?></title><?cs
  /if ?>
  <link><?cs var:base_host ?><?cs var:trac.href.blog ?></link>
  <description><?cs var:project.descr ?></description>
  <language>en-us</language>
  <generator>Trac v<?cs var:trac.version ?></generator><?cs
  if:chrome.logo.src ?>
   <image>
    <title><?cs var:project.name_encoded ?></title>
    <url><?cs if:!chrome.logo.src_abs ?><?cs var:base_host ?><?cs /if ?><?cs
     var:chrome.logo.src ?></url>
    <link><?cs var:base_host ?><?cs var:trac.href.blog ?></link>
   </image><?cs
  /if ?><?cs
  each:bentry = blog.entries ?>
   <item>
    <title><?cs var:bentry.title ?></title><?cs
    if:bentry.author.email ?>
     <author><?cs var:bentry.author.email ?></author><?cs
    else ?>
     <author><?cs var:bentry.author ?></author><?cs
    /if ?>
    <pubDate><?cs var:bentry.date ?></pubDate>
    <link><?cs var:base_host ?><?cs var:bentry.href ?></link>
    <guid><?cs var:base_host ?><?cs var:bentry.href ?></guid>
    <description>
      <?cs var:bentry.rss_text ?><?cs 
      if bentry.tags.present != 0 ?>
        &lt;p&gt;Posted in: <?cs
        each:tag=bentry.tags.tags ?>
          &lt;a href="<?cs if cgi_location != "/" ?><?cs var:cgi_location ?><?cs /if ?>/tags/<?cs var:tag.link ?>"&gt;
            <?cs var:tag.name ?>&lt;/a&gt;<?cs
          if ! tag.last ?>,<?cs 
          /if ?><?cs
        /each ?>&lt;/p&gt;<?cs
      /if ?>
    </description>
   </item><?cs
  /each ?>
 </channel>
</rss>
