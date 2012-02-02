$(document).ready(function() {
	jQuery('#changelog > div > form').each(function() {
		$(this).parent().find('h3').prepend(this);
	});
	jQuery('#changelog form.hidefieldchanges').each(function() {
		fieldname = $(this).parent('li').find('strong').text();
		$(this).addClass(fieldname);
		$(this).find('.hidebutton').attr('value','hide ' + fieldname);
	});
	jQuery('#hidechangesbutton').click(function() {
		jQuery('#hidefields').show();
	});
// jQuery('#changelog').prev().
	jQuery('#changelog div.change ul.changes li').each(function() {
		$(this).mouseover(function() {$(this).css('color','blue').find('.hidebutton').show()});
		$(this).mouseout (function() {$(this).css('color',''    ).find('.hidebutton').hide()});
	});
})