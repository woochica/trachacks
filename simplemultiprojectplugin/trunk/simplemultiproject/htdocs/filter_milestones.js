function smp_updateMilestones(newOptions, selectedOption)
{
    var select = $('#field-milestone');
    if(select.prop) {
      var options = select.prop('options');
    }
    else {
      var options = select.attr('options');
    }
    //$('option', select).remove();
    //$('optgroup', select).remove();
    select.empty();
    
    if (selectedOption && !newOptions[selectedOption]) {
        options[options.length] = new Option(selectedOption, selectedOption, true, true);
    }
        
    $.each(newOptions, function(val, text) {
        options[options.length] = new Option(val, text);
    });

    if (selectedOption) {
        var option = $('#field-milestone option:contains("' + selectedOption + '")');
        if (option) {
            if (option.prop) {
                option.prop('selected', true);
            } else {
                option.attr('selected', 'selected');
            }
        }
    }
}

function smp_onProjectChange(project)
{
    if (!project) {
        project = smp_initialProjectMilestone[0];
    }

    var milestones = smp_milestonesForProject[project];
    var selectedMilestone = "";

    if (project == smp_initialProjectMilestone[0]) {
        selectedMilestone = smp_initialProjectMilestone[1];
    }
    smp_updateMilestones(milestones, selectedMilestone);
}

jQuery(document).ready(function($) {
    smp_onProjectChange()
});
