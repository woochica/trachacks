function setSearchValues()
{
    var monthSelect = document.getElementById('Month');
    var daySelect = document.getElementById('Day');
    var yearSelect = document.getElementById('Year');
    var authorSelect = document.getElementById('author');
    var statusSelect = document.getElementById('status');
    var textField = document.getElementById('name');
    nameSelected = nameSelected.replace('/&lt;/g', '<');
    nameSelected = nameSelected.replace('/&gt;/g', '>');
    nameSelected = nameSelected.replace('/&#34;/g', '"');
    nameSelected = nameSelected.replace('/&amp;/g', '&');
    textField.value = nameSelected;

    for(var i = 0; i < monthSelect.options.length; i++)
    {
        if(monthSelect.options[i].value == monthSelected)
        {
            monthSelect.options[i].selected = 'true';
            break;
        }
    }

    for(var i = 0; i < yearSelect.options.length; i++)
    {
        if(yearSelect.options[i].value == yearSelected)
        {
            yearSelect.options[i].selected = 'true';
            break;
        }
    }

    dateIndexSelected = daySelected;
    resetDays(monthSelected, yearSelected);

    for(var i = 0; i < authorSelect.options.length; i++)
    {
        if(authorSelect.options[i].value == authorSelected)
        {
            authorSelect.options[0].selected = 'false';
            authorSelect.options[i].selected = 'true';
            break;
        }
    }
    for(var i = 0; i < statusSelect.options.length; i++)
    {
        if(statusSelect.options[i].value == statusSelected)
        {
            statusSelect.options[0].selected = 'false';
            statusSelect.options[i].selected = 'true';
            break;
        }
    }
}

function setDateIndex()
{
    dateIndexSelected = (document.getElementById('Day')).value;
    document.getElementById('dayHolder').value = dateIndexSelected;
}

function resetDays(month, year)
{
    var numDays = 0;
    var date = new Date();
    date.setFullYear(year, month - 1, 31);
    numDays = date.getDate();
    if(numDays < 4)
    {
        numDays = 31 - numDays;
    }
    setOptionText(document.getElementById('DaySpan'), numDays);
    setDateIndex();
}

function setOptionText(control, numDays)
{
    var innerHTML = '<select name=\"DateDay1\" id=\"Day\" onChange=\"setDateIndex();\">';
    innerHTML += '<option value = \"0\">Select...</option>';
    var day = '';

    for(var loop=1; loop <= numDays; loop++)
    {
        day = '';
        if(loop < 10)
        {
            day = '0'; //add a 0 to day so that all days are 2 digits - 01, 02, etc.
        }
        if(day + '' + loop == dateIndexSelected)
        {
            innerHTML += '<option selected="selected" value="' + day + loop + '">' + loop + '</option>\n';
        }
        else
        {
            innerHTML += '<option value="' + day + loop + '">' + loop + '</option>\n';
        }
    }

    innerHTML += '</select>';

    control.innerHTML = innerHTML;
}
