Array.prototype.has = function(v) {
    for (var i = 0; i < this.length; i++) {
        if (this[i] == v) {
            return true;
        }
    }
    return false;
} 

function smp_updateSelect(id, newOptions, selectedOption)
{
    var field_id = '#field-' + id;
    var select = $(field_id);
    if(select.prop) {
      var options = select.prop('options');
    }
    else {
      var options = select.attr('options');
    }
    select.empty();
    
    $.each(newOptions, function(val, text) {
        options[options.length] = new Option(text);
    });

    if (selectedOption) {
        if (!newOptions[selectedOption] && !newOptions.has(selectedOption)) {
            options[options.length] = new Option(selectedOption, selectedOption, true, true);
        } else {
            var option = $(field_id + ' option:contains("' + selectedOption + '")');
            if (option) {
                if (option.prop) {
                    option.prop('selected', true);
                } else {
                    option.attr('selected', 'selected');
                }
            }
        }
    }
}

function smp_onProjectChange(project)
{
    if (!project) {
        project = smp_initialProjectMilestone[0];
    }

    // milestones
    var milestones = smp_milestonesForProject[project];
    var selectedMilestone = "";

    if (project == smp_initialProjectMilestone[0]) {
        selectedMilestone = smp_initialProjectMilestone[1];
    }
    smp_updateSelect('milestone', milestones, selectedMilestone);

    // components
    var components = smp_all_components;
    var cur_comp = $('#field-component option:selected').text();
    var filtered_components = []
    
    for (var i = 0; i < components.length; i++) {
        var comp = components[i];
        if (!smp_component_projects[comp] || smp_component_projects[comp].has(project)) {
            filtered_components.push(comp)
        }
    }

    if (!cur_comp || cur_comp == "") {
        cur_comp = smp_default_component;
    }
    
    smp_updateSelect('component', filtered_components, cur_comp);

    // versions
    smp_updateSelect('version', smp_project_versions[project], smp_default_version)
}

jQuery(document).ready(function($) {
    smp_onProjectChange()
});
