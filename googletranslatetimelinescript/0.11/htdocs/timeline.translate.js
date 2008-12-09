// Translate changeset comments in Trac timeline
// Using Google Language API version 1

// Code in public domain
// techtonik // rainforce.org


// wrap the code to use $ as jQuery function name
(function($){


// setup language parameters

var srclang = "ru";
var tgtlang = "en";

var gtrans_btn_text = "Translate russian comments";

var srclang_a_z = Array();
srclang_a_z["en"] = /[a-z]+/i;
srclang_a_z["ru"] = /[Ð°-Ñ_]+/i;


// load Google API

google.load("language", "1");


// make this anonymous function executed by jQuery when document is loaded
jQuery(document).ready(function() {

    // add "powered by Google" logo into footer
    $('<p id="googleattr" class="left"></p>').insertAfter("#footer p.left:last")
    google.language.getBranding('googleattr');

    // add trac_timeline_translate() button to timeline menu
    var gtrans_btn = $("<input type='button'/>")
          .attr({
              id: "gtrans_btn",
              value:gtrans_btn_text
          })
          .click(function() {
              trac_timeline_translate();
              gtrans_btn.attr("disabled", "disables");
              return false;
          });

    $("#prefs").append("<hr/>");
    $("#prefs")
      .append(
         $("<div align='center'></div>").append(gtrans_btn)
      )
})


function trac_timeline_translate() {
    // translate changeset messages
    g_trans_nodes( $("dd.changeset") );
}


function g_trans_nodes(nodes) {
  // translate nodes one by one
  // todo: group many small nodes into one packet < 5000 bytes

  var transTexts = Array();
  var transNodes = Array();

  for (i=0; i<nodes.size();i++) {
      var text = nodes[i].innerHTML;

      if (text.match(srclang_a_z[srclang])) {
          transTexts.push(text);
          transNodes.push(nodes[i]);
      }
  }

  for (i=0; i<transTexts.length;i++) {
      function makeTransNodeClosure(target_node) {
          // closure to save node parameter to be accessible
          // in callback function
          var node = target_node; // local variable
          var trans_callback = function (result) {
              node.innerHTML = result.translation;
          }
          return trans_callback; // return function
      }
      
      google.language.translate(transTexts[i], srclang, tgtlang, makeTransNodeClosure(transNodes[i]));
    }
}


})(jQuery);
