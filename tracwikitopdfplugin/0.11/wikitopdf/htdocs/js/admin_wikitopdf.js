function move_item(from, to) {
    var from_box = document.getElementById(from+'pages_select');
    var to_box = document.getElementById(to+'pages_select');
    for (var i = 0; i < from_box.options.length; i++) {
       var opt = from_box.options[i];
       if (opt.selected) {
           var newOpt = new Option( opt.text, opt.value );
           try {
               to_box.add(newOpt, null); // standards compliant
           }
           catch (ex) {
               to_box.add(newOpt);       // MSIE
           }
           from_box.remove(i);
           i--;
       }
    }
}

function reorder_item(from, dir) {
    var box = document.getElementById(from+'pages_select');
    var i = box.selectedIndex;
    var j = i + dir;
    if(j<0 || j>=box.options.length) { return }
    var temp = box.options[i];
    var temp2 = box.options[j];
    box.options[i] = new Option(temp2.value, temp2.value);
    box.options[j] = new Option(temp.value, temp.value);
    box.selectedIndex = j;
}

function compile_pages(form) {
    var arr = new Array();
    for(i=0;i<form.rightpages.options.length;i++) {
        arr.push(form.rightpages.options[i].value);
    }
    form.rightpages_all.value = arr.join(',');
    return 1;
}
