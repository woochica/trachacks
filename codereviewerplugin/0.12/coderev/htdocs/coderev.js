// add the codereviewer form to existing changeset page
var setup = function(){
    var review = get_review();
    var status_choices = get_status_choices();
    
    // add a "warning" to the page
    var class_ = is_pending() ? ' pending' : '';
    var html = '<div class="system-message'+class_+'" id="message">'
              +'Code review status is <strong>'+href(review.status)+'</strong>. '
              +'Update status and view/add a summary '+href("below")+'.'
              +'</div>';
    jQuery('#ctxtnav').after(html);
    
    // begin review status form
    html = '<form id="codereviewform" action="'+window.location.href+'" method="POST">'
          +'<h1 id="codereview">Code Review</h1>'
          +'<dl id="review">'
          +'  <dt class="property">Review summary:</dt>';
    
    // add past summaries
    jQuery(review.summaries).each(function(i,summary){
        html += '<dd><h3 class="summary">'+summary.reviewer;
        if (summary.status.length)
            html += ' set to '+summary.status;
        else
            html += ' commented';
        html += ' on '+summary.pretty_when+'</h3>'+decode(summary.html_summary)+'<br/></dd>';
    });
    
    // link to tickets if just saved comments
    var tickets = get_tickets();
    if (tickets.length){
        var s = tickets.length == 1 ? '' : 's';
        html += '<dd><div class="system-message notice">Saved status and added comment to ticket'+s+' ';
        jQuery(tickets).each(function(i,ticket){
            html += '<a href="/ticket/'+ticket+'">#'+ticket+'</a>';
            if (i < tickets.length-1)
                html += ', ';
        });
        html += '</div></dd>';
    }
    
    // add new summary fields and finish form
    html += '  <dd><textarea id="review-summary" name="summary" rows="10" cols="78"/></dd>'
           +'  <dt class="property">Review status:</dt>'
           +'  <dd><select id="review-status" name="status">';
    jQuery(status_choices).each(function(i,choice){
        html += '<option';
        if (choice == review.status)
            html+= ' selected="selected"';
        html += ' value="'+choice+'">'+choice+'</option>';
    });
    html += '  </select>'
           +'  <input type="submit" id="reviewbutton" name="reviewbutton" value="Submit review"/></dd>'
           +'  <input type="hidden" name="__FORM_TOKEN" value="'+get_form_token()+'"/></dd>'
           +'</dl>'
           +'</form>';
    jQuery('div.diff:last').after(html);
}

// utils
var decode = function(encoded){
    return encoded.replace(/&lt;/g,"<").replace(/&gt;/g,">");
}

var href = function(text){
    return '<a href="#codereview" title="View/edit code review">'+text+'</a>';
}

var get_url = function(){
    return jQuery('link[rel="search"]').attr('href').replace(/\/search/, '');
}
