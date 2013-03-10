/*
 * Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
  
  if (typeof _ == 'undefined') 
    babel.Translations.load({}).install();

  function addAnchor(target, name) {
    $(target)
      .css('position', 'relative')
      .attr("id", name);
    $("<a>\u00B6</a>")
      .addClass('anchor')
      .addClass('trac-anchoranywhere-prepend')
      .attr("href", "#" + name)
      .attr("title",_("Link here"))
      .prependTo(target);
  }
  
  $(document).ready(function() {
    $("#ticket .properties td[headers] p, #ticket .properties td[headers] li").each(function() {
      context = $(this).parents('td[headers]');
      index = 1 + $("p,li", context).index(this);
      name = context.attr('headers').slice(2) + "|" + index;
      addAnchor(this, name);
    });
    $("#ticket .description p, #ticket .description li").each(function() {
      context = $(this).parents('div.searchable');
      index = 1 + $("p, li", context).index(this);
      name = "description|" + index;
      addAnchor(this, name);
    });
    $("#changelog p, #changelog li").each(function() {
      context = $(this).parents('div.change');
      index = 1 + $("p,li", context).index(this);
      name = $('.cnum', context).attr('id') + "|" + index;
      addAnchor(this, name);
    });
  
    $("#wikipage p, #wikipage li").each(function() {
      name = this.id;
      if (name == "") {
        // generate a unique name
        last = $(this);
        while (true) {
          context = last.prevAll("h1,h2,h3,h4,h5,h6[id]").first();
          if (context.length != 0) { // found headings
            name = (context.attr('id') || "") + "|"
                + (1 + context.nextAll().index(last)) + name;
            break;
          } else if (last[0].id == 'wikipage' ||
                     last.index() == -1 ||
                     name.length > 100) {  // Sentinel
            name = (context.attr('id') || "") + "|" + name.slice(1);
            break;
          }
          name = "." + (1 + last.index()) + name;
          last = last.parent();
        }
      }
      addAnchor(this, name);
    });
    
  }); // end of document.ready
})(jQuery);
