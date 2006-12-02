$(function() {
    var username = $('#fakeusername_evil').text();
    $('#newticket').prepend('<div class="field"><label for="reporter">Your email or username:</label><br /><input type="text" id="reporter" name="reporter" size="40" value="'+username+'" /><br /></div>');
});
