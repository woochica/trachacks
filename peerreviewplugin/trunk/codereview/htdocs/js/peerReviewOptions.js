//Ensure a correct percentage is input
function validateInput() {
    var perEl = document.getElementById('percentBox');
    var val = parseInt(perEl.value);
    if ((val != perEl.value-0) || val < 0 || (val > 100)) {
        alert("You must specify an integer percentage between 0 and 100.");
        return false;
    } else {
        document.getElementById('percentage').value = val;
        return document.getElementById('thresholdForm').submit();
    }
}