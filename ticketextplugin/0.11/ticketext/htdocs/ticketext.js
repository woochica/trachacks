/**
 * i18n
 */
var Localizer = function() {
    this.strings = {};
    this.lang = "?";
    
    var htmlTag = document.getElementsByTagName("html")[0];
    this.lang = htmlTag.getAttribute("xml:lang") || htmlTag.getAttribute("lang");
    
    // If there isn't the lang attribute, use browser language.
    if (this.lang == null || this.lang == "") {
        var currentLanguage;
        if (navigator.browserLanguage) {
            currentLanguage = navigator.browserLanguage; 
        } else if (navigator.language) { 
            currentLanguage = navigator.language; 
        } else if (navigator.userLanguage) { 
            currentLanguage = navigator.userLanguage; 
        }
        
        if (currentLanguage && currentLanguage.length >= 2) {
            this.lang = currentLanguage.substr(0,2);
        }
    }
    
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
                                  "編集中の説明の内容は破棄されますが、よろしいですか？",
    
    // end
    "end" : ""
};


/**
 * Apply the template to a trac ticket.
 * 
 * @param typeIdValue The ticket type element id.
 * @param descIdValue The ticket description element id.
 */
var TicketTemplate = function(baseUrlValue, typeIdValue, descIdValue) {
        
    this.STYLE_CLASS_EXCLUDE = "te_exclude";
    this.DELIM               = ",";
    
    this.baseUrl          = "/";
    this.typeId           = "type";
    this.descId           = "template";
    this.enablefieldsId   = "enablefields";
    
    // trac default field name
    // "__EDITOR__1" is for TracWysiwygPlugin
    this.defaultPropArray = ["field_summary", "field_reporter", "field_description",
                             "field_owner", "field_type", "field_priority", "field_milestone",
                             "field_component", "field_version", "field_keywords", "field_cc",
                             "__EDITOR__1"];
    
    if (baseUrlValue) {
        this.baseUrl = baseUrlValue;
    }
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
    
    // Apply template at the first time.
    // except preview
    var previewFieldsElem = document.getElementById("preview");
    if (!previewFieldsElem || previewFieldsElem.tagName != "FIELDSET") {
        this.selectTemplate(typeElem);
    }
    
    $(typeElem).change(this.changeType(typeElem));
};

/**
 * This is called when the ticket type changed.
 * 
 * @param typeElem The ticket type element.
 */
TicketTemplate.prototype.changeType = function(typeElem) {
    var self = this;
    
    var func = function(event) {
        var isProceed = confirm(_("template.confirm.clear")); 
        if (!isProceed) {
            return;
        }
        
        self.selectTemplate(typeElem);
    };
    
    return func;
};

/**
 * Select the ticket template.
 * 
 * @param typeElem The ticket type element.
 */
TicketTemplate.prototype.selectTemplate = function(typeElem) {
    var self = this;
    
    var selectedIndex = typeElem.selectedIndex;
    var typeValue = typeElem.options[selectedIndex].text;
    
    var reqUrl = this.baseUrl + "/ticketext/template?"
               + "type=" + encodeURI(typeValue)
               + "&timestamp=" + (new Date()).getTime();
    
    var responseData;
    $.ajax({
        type: "GET",
        url: reqUrl,
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
 * 
 * @param Template data object of TicketExt.
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
 * 
 * @param Template data object of TicketExt.
 */
TicketTemplate.prototype.applyDescription = function(templateData) {
    // change description value
    var descElem = document.getElementById(this.descId);
    if (!descElem) {
        return;
    }
    
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
    
    descElem.value = templateValue;
    
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
 * 
 * @param Template data object of TicketExt.
 */
TicketTemplate.prototype.applyCustomfields = function(templateData) {
    
    var enablefieldsValue = templateData.enablefields;
    if (!enablefieldsValue || jQuery.trim(enablefieldsValue).length <= 0) {
        enablefieldsValue = "";
    }
    
    // custom fields array
    var enableFieldArray = templateData.enablefields.split(this.DELIM);
    for (var index = 0; index < enableFieldArray.length; index++) {
        enableFieldArray[index] = "field_" + jQuery.trim(enableFieldArray[index]);
    }
    
    // all fields array
    var enablePropArray = this.defaultPropArray.concat(enableFieldArray);
    
    this.applyCustomfieldsForAdmin(enablePropArray);
    this.applyCustomfieldsForTicket(enablePropArray);
}

/**
 * Set the custom fields enable or disable at the admin page.
 * 
 * @param enablePropArray Enable property array
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
 * 
 * @param enablePropArray Enable property array.
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
        var strIndex = enablePropJoin.indexOf(propElem.name + this.DELIM);
        
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
 * 
 * @param typeId The ticket type element id.
 * @param descId The ticket description element id.
 */
TicketTemplate.initialize = function(baseUrl, typeId, descId) {
    var ticketTemplateObj = new TicketTemplate(baseUrl, typeId, descId);
};
