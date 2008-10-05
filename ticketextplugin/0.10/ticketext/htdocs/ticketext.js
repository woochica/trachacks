/**
 * i18n
 */
var Localizer = function() {
    this.strings = {};
    this.lang = "?";
    
    var htmlTag = document.getElementsByTagName("html")[0];
    this.lang = htmlTag.getAttribute("xml:lang") || htmlTag.getAttribute("lang");
    
    var self = this;
    this.getLocalizedString = function(key) {
        var message = Localizer.strings[key + "_" + self.lang];
        if (!message || message == "") {
            message = Localizer.strings[key];
        }
        return message;
    };
    
    return this;
}

Localizer = new Localizer();
_ = Localizer.getLocalizedString;

Localizer.strings = {
    // default
    "template.confirm.clear" : "Apply the template to the description." + "\n" +
                               "The description will be clear, but you sure?",
    
    // ja
    "template.confirm.clear_ja" : "説明の内容にテンプレートを適用します。\n" +
                                  "編集中の説明の内容は破棄されますが、よろしいですか？"
};


/**
 * Apply the template to a trac ticket.
 */
var TicketTemplate = function(typeIdValue, descIdValue) {
        
    this.STYLE_CLASS_EXCLUDE = "te_exclude";
    this.DELIM               = ",";
    
    this.typeId           = "type";
    this.descId           = "template";
    this.enablefieldsId   = "enablefields";
    this.defaultPropArray = ["priority", "milestone", "component", "version", "keywords", "owner", "cc"];
    
    if (typeIdValue) {
        this.typeId = typeIdValue;
    }
    if (descIdValue) {
        this.descId = descIdValue;
    }
    
    var typeElem = document.getElementById(this.typeId);
    if (!typeElem) {
        return;
    }
    
    this.selectTemplate(typeElem);
    $(typeElem).change(this.changeType(typeElem));    
};

/**
 * This is called when the ticket type changed.
 */
TicketTemplate.prototype.changeType = function(typeElem) {
    var self = this;
    
    return function(event) {
        var isProceed = confirm(_("template.confirm.clear")); 
        if (!isProceed) {
            return;
        }
        
        self.selectTemplate(typeElem);
    };
};

/**
 * Select the ticket template.
 */
TicketTemplate.prototype.selectTemplate = function(typeElem) {
    var self = this;
    
    var selectedIndex = typeElem.selectedIndex;
    var typeValue = typeElem.options[selectedIndex].text;
    
    var prjUriLastIndex = (location.pathname).indexOf("/", 1);
    var prjUri = (location.pathname).substring(0, prjUriLastIndex);
    
    var responseData;
    $.ajax({
        type: "GET",
        url: prjUri + "/ticketExtTemplate?type=" + encodeURI(typeValue),
        async: false,
        success: function(jsonData){
            var responseData;
            if (typeof(jsonData) == "string") {
                responseData = eval("(" + jsonData + ")");
            } else {
                responseData = eval("(" + jsonData.responseText + ")");
            }
            
            self.applyTemplate(responseData);
        }
    });
    
};

/**
 * Apply the template to the ticket.
 */
TicketTemplate.prototype.applyTemplate = function(templateData) {
    if (!templateData) {
        return;
    }

    this.applyDescription(templateData);
    this.applyCustomfields(templateData);
}

/**
 * Apply the description template to the ticket.
 */
TicketTemplate.prototype.applyDescription = function(templateData) {
    // change description value
    var descElem = document.getElementById(this.descId);
    var templateValue = templateData.template;
    
    // if TracWysiwygPlugin is used,
    // it must be chnage edit mode before change the description value.
    var enableWysiwyg = false;
    var editorMode;
    var textareaModeElem;
    var wysiwygModeElem;
    
    if(typeof TracWysiwyg == "function") {
        enableWysiwyg = true;
    }
    
    if (enableWysiwyg) {
        editorMode = TracWysiwyg.getEditorMode();
        textareaModeElem = document.getElementById("editor-textarea-1");
        wysiwygModeElem = document.getElementById("editor-wysiwyg-1");
        
        if (editorMode != "textarea" && textareaModeElem) {
            textareaModeElem.click();
        }
    }
    
    if (descElem && templateValue) {
        descElem.value = templateValue;
    }
    
    if (enableWysiwyg) {
        switch (editorMode) {
        case "textarea":
            if (textareaModeElem) {
                textareaModeElem.click();
            }
            break;
        case "wysiwyg":
            if (wysiwygModeElem) {
                wysiwygModeElem.click();
            }
            break;
        default:
           break;
        }
    }
}

/**
 * Apply the custom fields template to the ticket.
 */
TicketTemplate.prototype.applyCustomfields = function(templateData) {
    
    var enablefieldsValue = templateData.enablefields;
    if (!enablefieldsValue || jQuery.trim(enablefieldsValue).length <= 0) {
        enablefieldsValue = "";
    }
    
    // custom fields array
    var enableFieldArray = templateData.enablefields.split(this.DELIM);
    for (var index = 0; index < enableFieldArray.length; index++) {
        enableFieldArray[index] = jQuery.trim(enableFieldArray[index]);
    }
    
    // all fields array
    var enablePropArray = this.defaultPropArray.concat(enableFieldArray);
    
    this.applyCustomfieldsForAdmin(enablePropArray);
    this.applyCustomfieldsForTicket(enablePropArray);
}

/**
 * Set the custom fields enable or disable at the admin page.
 */
TicketTemplate.prototype.applyCustomfieldsForAdmin = function(enablePropArray) {
    var fieldsElem = document.getElementsByName("cf-enable");
    if (fieldsElem.length <= 0) {
        return;
    }
    
    var enablePropJoin = enablePropArray.join(this.DELIM) + this.DELIM;
    
    for (var index = 0; index < fieldsElem.length; index++) {
        var cfenable = fieldsElem[index];
        if (cfenable.value) {
            var strIndex = enablePropJoin.indexOf(cfenable.value + this.DELIM);
            if (strIndex > 0) {
                cfenable.checked = true;
            } else {
                cfenable.checked = false;
            }
        }
    }
}

/**
 * Set the custom fields enable or disable at the ticket page.
 */
TicketTemplate.prototype.applyCustomfieldsForTicket = function(enablePropArray) { 
    var fieldsElem = document.getElementById("properties");
    if (!fieldsElem) {
        return;
    }
        
    var enablePropJoin = enablePropArray.join(this.DELIM) + this.DELIM;
        
    // disable field
    var propArray = [];
    
    // input field
    var inputElemArray = fieldsElem.getElementsByTagName("INPUT");
    for (var index = 0; index < inputElemArray.length; index++) {
        var inputType = inputElemArray[index].type;
        if (inputType.match("(text)|(checkbox)|(radio)|(file)")) {
            propArray.push(inputElemArray[index]);
        }
    }
    
    // select field
    var selectElemArray = fieldsElem.getElementsByTagName("SELECT");
    for (var index = 0; index < selectElemArray.length; index++) {
        propArray.push(selectElemArray[index]);
    }
    
    // textarea field
    var textareaElemArray = fieldsElem.getElementsByTagName("TEXTAREA");
    for (var index = 0; index < textareaElemArray.length; index++) {
        propArray.push(textareaElemArray[index]);
    }
    
    for (var index = 0; index < propArray.length; index++) {
        var propElem = propArray[index];
        var strIndex = enablePropJoin.indexOf(propElem.id + this.DELIM);
        
        propElem.className = propElem.className.replace(this.STYLE_CLASS_EXCLUDE, "");
        if (strIndex >= 0) {
            propElem.disabled = false;
        } else {
            propElem.disabled = true;
            propElem.className = propElem.className + " " + this.STYLE_CLASS_EXCLUDE;
        }
    }
}

/**
 * Initialize TicketTemplate.
 */
TicketTemplate.initialize = function(typeId, descId) {
    var ticketTemplateObj = new TicketTemplate(typeId, descId);
};
