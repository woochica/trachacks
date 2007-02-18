function on_projectmenu_change() {
    var s = document.getElementById('projectmenu');
    if(s.value != '') {
        window.location = s.value;
    }
}