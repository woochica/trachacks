$(document).ready(function() {
    $("#hide").click(function () {
        var text = $("#hide").text();
        if (text.search(/show/) >= 0) {
            $("#hide").text('hide six hats introduction')
            $("#introduction").show();
        } else {
            $("#hide").html('show six hats introduction');
            $("#introduction").hide();
        }
    });
});
