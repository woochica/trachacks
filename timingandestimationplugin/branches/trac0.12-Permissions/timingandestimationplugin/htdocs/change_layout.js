// Move the add hours box next to the comment box
var TandE_MoveAddHours = function(){
  // Couldnt find the comment box, lets just abort
  if ($('#comment').length == 0) return;
  var tbl, hours, colClass, tr, replacement;
  tbl = $('<table style="border:1px solid #D7D7D7;" border="0" cellpadding="3" cellspacing="0"><tbody><tr></tr></tbody></table>');
  $('#comment').parent().parent().after(tbl);
  hours = $('#field-hours');
  colClass = hours.parent().attr("class");
  tr = hours.parent().parent();
  $(tbl[0].rows[0]).append($('.'+colClass, tr));
  replacement = $('<td class="'+colClass+'"></td>');
  tr.prepend(replacement.clone()).prepend(replacement.clone());
};

/*
 * Rewritten by Russ Tyndall when this started failing on Trac 1
 *
 *   Code by Josh Godsiff, for www.oxideinteractive.com.au
 *   Email: josh@oxideinteractive.com.au
 */
$.prototype.cleanupTable = function() {
    // make sure that body
    if($(this).is('table')) {
        var bodies = $(this).children('thead, tbody, tfoot');
    } else if($(this).is('thead, tbody, tfoot')) {
        var bodies = $(this);
    } else {
        return;
    }
    // helper to determine if a table cell has visible content
    var has_contents =function(it){
      var t=$(it).text();
      if(t && $.trim(t).length>0 ) return true;
      return false;
    };

    $(bodies).each(function(bodyIdx, body){
      body = $(body);
      var trs = $(body).children('tr');
      var leftTds = [], rightTds = [], extraTDs=[];
      $(trs).each(function(ind, val){
        var kids = $(this).children();

        // special case for things that get removed badly (eg: CondFieldsGenshiPlugin)
        // this is a two cell row in a table full of 4 cell rows
        if(kids.length == 2 && !$(kids[1]).is('.fullrow')){
          $(this).detach();
          extraTDs.push([kids[0], kids[1]]);
        }
        else if(kids.length == 4){
          $(this).detach();
          if(has_contents(kids[0]) || has_contents(kids[1]))
            leftTds.push([kids[0], kids[1]]);
          //else console.log('skipping empty', kids);
          if(has_contents(kids[2]) || has_contents(kids[3]))
            rightTds.push([kids[2], kids[3]]);
          //else console.log('skipping empty', kids);
        };
      });
      //console.log(leftTds,rightTds, extraTDs);
      while(leftTds.length>0 || rightTds.length>0 || extraTDs.length>0){
        var tr = $('<tr>');
        var leftContent = leftTds.shift() || extraTDs.shift() || [$("<td>"),$("<td>")];
        var rightContent = rightTds.shift() || extraTDs.shift() || [$("<td>"),$("<td>")];
        tr.append(leftContent[0]).append(leftContent[1])
          .append(rightContent[0]).append(rightContent[1]);
        $(body).append(tr);
      }
    });
};

$(document).ready(function() {
   // Give other layout changing functions time to run

  // move add hours input to next to the comment box
  TandE_MoveAddHours();
  // remove add_hours from header
  $('#h_hours,#h_hours + td').empty();
  $('#h_hours,#h_hours + td').detach();

  //remove whitespace caused by the above
  $('#properties table').cleanupTable();
  $('table.properties').cleanupTable();

});
