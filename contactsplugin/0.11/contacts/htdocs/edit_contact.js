jQuery(document).ready(function() {
    jQuery('.static, .field label').click(function() {
        p = jQuery(this).parent()
        p.children('.edit').show()
        p.children('.static').hide()
    });
    jQuery('input.revert').click(function() {
        p = jQuery(this).parent()
        p.children('.edit').hide()
        p.children('.static').show()
        
        p.children('.edit.value').attr('value', jQuery(this).next('.static').text())
    });
})
