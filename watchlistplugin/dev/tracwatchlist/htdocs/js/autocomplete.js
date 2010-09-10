/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.js $
 * */

jQuery(document).ready(function() {
  // Autocomplete Wiki Names
  var asWikiNames = [];
  $("table#wikilist tbody td.name").each(function () {
      asWikiNames.push( $(this).text().replace(/^\s*|\s*$/g,'') );
  });
  $("#wikis .remfromwatch input[name=resid]")
      .autocomplete(asWikiNames);
  $("#wikis tfoot th.name input")
      .autocomplete(asWikiNames);
  $("#wikis .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=wiki");
  ///
  var asAuthors = new Object();
  $("table#wikilist tbody td.author").each(function () {
      asAuthors[ $(this).text().replace(/^\s*|\s*$/g,'') ] = 1;
  });
  alert( asAuthors.keys() );

  // Autocomplete Ticket Ids
  var asTicketIds = [];
  $("table#ticketlist tbody td.id").each(function () {
      asTicketIds.push( $(this).text().replace(/^\s*#|\s*$/g,'') );
  });
  $("#tickets .remfromwatch input[name=resid]")
      .autocomplete(asTicketIds);
  $("#tickets .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=ticket");
  asWikiNames = [];
  asTicketIds = [];
  ///
});


