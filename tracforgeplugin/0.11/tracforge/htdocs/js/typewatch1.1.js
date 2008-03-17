/*
 *  TypeWatch 1.1.1
 *  jQuery 1.1.3 +
 *  
 *  Examples/Docs: www.dennydotnet.com
 *  Copyright(c) 2007 Denny Ferrassoli
 * Dual licensed under the MIT and GPL licenses:
 * http://www.opensource.org/licenses/mit-license.php
 * http://www.gnu.org/licenses/gpl.html
*/

jQuery.fn.extend({
  typeWatch:function(options) {
    var typewatch_uid = 0; // unique counter
    var typewatch_data = {};
    
    function typewatchCheck( thisWinSaved, override ) {
      var timer = typewatch_data[thisWinSaved];
      var elTxt = $(timer.el).val();

      if (elTxt.toUpperCase() != timer.text || override) {
        timer.text = elTxt.toUpperCase();
        timer.cb(elTxt);
      }
    }
    
    this.each(

      function() {

        // Set to current element
        thisEl = jQuery(this);
        var winSaved = "typewatch_" + typewatch_uid++;
        var objWatch = {timer:null, text:null, cb:null, el:null, wait:null};

        // Create js prop
        this.typewatchid = winSaved;

        // Must be text or textarea
        if (this.type.toUpperCase() == "TEXT" 
          || this.nodeName.toUpperCase() == "TEXTAREA") {

          // Allocate timer element
          typewatch_data[winSaved] = objWatch;
          var timer = typewatch_data[winSaved];

          // Defaults
          var _wait = 750;
          var _callback = function() { };
          var _highlight = true;
          var _captureEnter = true;

          // Get options
          if (options) {
            if(options["wait"] != null) _wait = parseInt(options["wait"], 10);
            if(options["callback"] != null) _callback = options["callback"];
            if(options["highlight"] != null) _highlight = options["highlight"];
            if(options["enterkey"] != null) _captureEnter = options["enterkey"];
          }

          // Set values
          timer.text = thisEl.val().toUpperCase();
          timer.cb = _callback;
          timer.wait = _wait;
          timer.el = this;

          // Set focus action (highlight)
          if (_highlight) {
            thisEl.focus(
              function() {
                this.select();
              });
          }

          // Key watcher / clear and reset the timer
          thisEl.keydown(
            function(evt) {
              var thisWinSaved = this.typewatchid;
              var timer = typewatch_data[thisWinSaved];

              // Enter key only on INPUT controls
              if (evt.keyCode == 13 && this.type.toUpperCase() == "TEXT") {
                clearTimeout(timer.timer);
                timer.timer = setTimeout(function() {typewatchCheck(thisWinSaved, true);}, 1);              
                return false;
              }

              clearTimeout(timer.timer);
              timer.timer = setTimeout(function() {typewatchCheck(thisWinSaved, false);}, timer.wait);
            });
        }
      });
  }
});



