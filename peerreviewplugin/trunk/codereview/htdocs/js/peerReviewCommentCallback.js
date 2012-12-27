function showHideAttachFile()
{
    var area = document.getElementById('FileUp');
    var area2 = document.getElementById('FileUpCompanion');
    if(area == null)
        return;

    if(area.style.display == "")
    {
        area.style.display = "none";
        area2.style.display = "none";

        area = document.getElementById('addCommentText');
        area.focus();
    }
    else
    {
        area.style.display = "";
        area2.style.display = "";
    }

    top.resetAddCommentBoxSize();
}

function submitComment(LineNum, fileID, parentID)
{
    var textField = document.getElementById('addCommentText');

    if(textField == null)
        return;

    if(textField.value == "")
    {
        alert("Please fill in the comment field.");
        return;
    }

    var fEle = document.getElementById('IDFile');
    var lEle = document.getElementById('LineNum');
    var tEle = document.getElementById('Text');
    var pEle = document.getElementById('IDParent');

    fEle.value = fileID;
    lEle.value = LineNum;
    tEle.value = textField.value;
    pEle.value = parentID;

    GLOBAL_line = LineNum;
    GLOBAL_parent = parentID;
    GLOBAL_file = fileID;

    textField.value = "";

    var formEle = document.getElementById('HiddenCommentForm');
    formEle.submit();
}

var GLOBAL_line = -1;
var GLOBAL_parent = -1;
var GLOBAL_file = -1;
