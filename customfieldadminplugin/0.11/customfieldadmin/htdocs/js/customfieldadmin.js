/**********
* User Interface function for Trac Custom Field Admin plugin.
* License: BSD
* (c) 2007-2009 ::: www.Optaros.com (cbalan@optaros.com)
**********/
(function($){
    function toggle_options(type_element){
        function label(property){ return $(property).parents('div.field')}
        switch (type_element.selectedIndex) {
            case 0: // text
                label('#options, #cols, #rows').hide();
                label('#format').show();
                break;
            case 1: // select
                label('#options, #cols, #rows').show();
                label('#format').hide();
                break;
            case 2: // checkbox
                label('#options, #cols, #rows').hide();
                label('#format').hide();
                break;
            case 3: // radio
                label('#options').show();
                label('#cols, #rows, #format').hide();
                break;      
            case 4: // textarea
                label('#options').hide();
                label('#cols, #rows, #format').show();
                break;
        }
    }
    
    $(document).ready(function(){
        $('#type').each(function(){
            toggle_options(this);
            $(this).change(function(){
                toggle_options(this);
            });
        });
    });
})(jQuery);
