(function($) {
    $(document).ready(function () {
        // Create a Table of Contents (TOC)
        $('#content .wikipage')
            .prepend('<div id="rpc-toc" class="wiki-toc"><h4>Contents</h4><ul /></div>');
        function toc_entry(_this, item) {
            return $('<li><a href="#' + _this.id + '" title="'
                     + $(item).text().replace(/^\s+|\s+$/g, '')
                     + '">' + _this.id.replace(/^rpc\./, '') + '</a></li>');
        }
        var ul = $('#rpc-toc ul');
        $("#content").find("*[id]").each(function(index, item) {
            var elem = undefined;
            if (this.tagName == 'H2') {
                elem = toc_entry(this, item);
                elem.css('padding-top', '0.5em');
            }
            if (this.tagName == 'H3') {
                elem = toc_entry(this, item);
                elem.css('padding-left', '1.2em');
            }
            ul.append(elem);
        });
        $('#rpc-toc').toggle();
        // Add anchors to headings
        $("#content").find("h2,h3").addAnchor("Link here");
    });
})(jQuery);
