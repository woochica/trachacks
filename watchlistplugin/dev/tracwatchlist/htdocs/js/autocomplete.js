/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.js $
 * */

jQuery(document).ready(function() {
  // Autocomplete Wiki Names
  var asWikiNames = [];
  $("table#wikilist").each(function(){
    $(this).find('tbody td.name').each(function () {
        asWikiNames.push( $(this).text().replace(/^\s*|\s*$/g,'') );
      });
  });
  $("#wikis .remfromwatch input[name=resid]")
      .autocomplete(asWikiNames);
  $("#wikis .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=wiki");
  ///

  // Autocomplete Ticket Ids
  var asTicketIds = [];
  $("table#ticketlist").each(function(){
    $(this).find('tbody td.id').each(function () {
        asTicketIds.push( $(this).text().replace(/^\s*#|\s*$/g,'') );
      });
  });
  $("#tickets .remfromwatch input[name=resid]")
      .autocomplete(asTicketIds);
  $("#tickets .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=ticket");
  asWikiNames = [];
  asTicketIds = [];
  ///
});


