jQuery(document).ready(function($) {
	$("#action_reassign_reassign_owner").autocomplete("../users", { 
		formatItem: formatItem 
		    }); 
});