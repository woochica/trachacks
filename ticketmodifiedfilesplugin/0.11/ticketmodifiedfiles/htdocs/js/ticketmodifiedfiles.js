<!--
	function togglevisibility(element) {
		if(element == "listofchangesets"){
		    if(document.getElementById(element).style.display=="block"){
                document.getElementById(element).style.display="none";
                document.getElementById("changesetslink").innerHTML="Display the list of changesets relative to this ticket.";
		    } else {
                document.getElementById(element).style.display="block";
                document.getElementById("changesetslink").innerHTML="Hide the list of changesets relative to this ticket.";
		    }
		}
        if(element == "checkboxes"){
            inputs = document.getElementsByTagName("input");
            actualvisibility = "";
            for(j=0; j<inputs.length; j++){
                if(inputs[j].getAttribute('class') == "helpcheckbox"){
                    if(inputs[j].style.display == "block"){
                        inputs[j].style.display = "none";
                    } else {
                        inputs[j].style.display = "block";
                    }
                    actualvisibility = inputs[j].style.display;
                }
            }
            if(actualvisibility == "block"){
                document.getElementById("togglecheckboxlink").innerHTML = "Hide the checkboxes";
            } else {
                document.getElementById("togglecheckboxlink").innerHTML = "Display the checkboxes";
            }
        }
	}
//-->