var ticketext;
if (!ticketext) ticketext = {};

// -----------------------------------------------------------------------------
// Localization
// -----------------------------------------------------------------------------

/**
 * i18n
 */
ticketext.Localizer = function() {
    this.strings = {};
    this.lang = "";
    
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
    this.getLocalizedString = function(str) {
        if (!ticketext.Localizer.strings)
        {
            return str;
        }
        
        var message = ticketext.Localizer.strings[str];
        if (!message || message == "") {
            message = str;
        }
        return message;
    };
    
    return this;
}

ticketext.Localizer = new ticketext.Localizer();
_ = ticketext.Localizer.getLocalizedString;


// -----------------------------------------------------------------------------
// TicketTemplate
// -----------------------------------------------------------------------------

/**
 * Apply the template to a trac ticket.
 * 
 * @param typeIdValue
 *            The ticket type element id.
 * @param descIdValue
 *            The ticket description element id.
 */
ticketext.TicketTemplate = function(baseUrlValue) {
    
    this.STYLE_CLASS_EXCLUDE = "te_exclude";
    this.STYLE_CLASS_CHANGED = "te_changed";
    this.DELIM               = ",";
    
    // for TracWysiwygPlugin Parameter
    this.WYSISYG_MAX_NUM       = 10;
    this.WYSISYG_EDITOR_PREFIX = "__EDITOR__";
    
    this.baseUrl           = "/";
    this.typeId            = "type";
    this.descId            = "template";
    this.enablefieldsId    = "enablefields";
    this.readyDescription  = false;
    this.readyCustomfields = true;
    
    // trac default field name
    this.defaultPropArray = ["field_summary", "field_reporter", "field_description",
                             "field_owner", "field_type", "field_priority", "field_milestone",
                             "field_component", "field_version", "field_severity", "field_keywords",                             "field_cc"];
    
    if (baseUrlValue) {
        this.baseUrl = baseUrlValue;
    }    
};

/**
 * Initialize TicketTemplate.
 */
ticketext.TicketTemplate.prototype.initialize = function() {
    var typeElem = document.getElementById(this.typeId);
    if (!typeElem) {
        return;
    }
    
    var descElem = document.getElementById(this.descId);
    if (!descElem) {
        return;
    }
    
    // Apply template at the first time.
    this.selectTemplate(typeElem);
    
    // if change type, change the template.
    $(typeElem).change(this.changeType(typeElem));
    
    // if change description, the css is changed for showing confirm dialog.
    var self = this;
    $(descElem).change(function() {
        if (!$(descElem).hasClass(self.STYLE_CLASS_CHANGED)) {
            $(descElem).addClass(self.STYLE_CLASS_CHANGED);
        }
    });
}

/**
 * This is called when the ticket type changed.
 * 
 * @param typeElem
 *            The ticket type element.
 */
ticketext.TicketTemplate.prototype.changeType = function(typeElem) {
    var self = this;
    
    var func = function(event) {
        var descElem = document.getElementById(self.descId);
        
        // check the change at the wysiwyg mode.
        if (!$(descElem).hasClass(self.STYLE_CLASS_CHANGED)) {
            var textBefore = $(descElem).text();
            
            var dummyFunc = function() {};
            self.execFunctionWithTracWysiwygPlugin(dummyFunc);
            
            var textAfter = $(descElem).text();
            
            if (textBefore != textAfter) {
                $(descElem).addClass(self.STYLE_CLASS_CHANGED);
            }
        }
        
        // show the dialog.
        if ($(descElem).hasClass(self.STYLE_CLASS_CHANGED)) {
            var isProceed = confirm(_("Apply the template to the description.\nThe description will be clear, but you sure?")); 
            if (!isProceed) {
                return;
            }
        }
        
        $(descElem).removeClass(self.STYLE_CLASS_CHANGED);
        
        self.selectTemplate(typeElem);
    };
    
    return func;
};

/**
 * Select the ticket template.
 * 
 * @param typeElem
 *            The ticket type element.
 */
ticketext.TicketTemplate.prototype.selectTemplate = function(typeElem) {
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
 * @param Template
 *            data object of TicketExt.
 */
ticketext.TicketTemplate.prototype.applyTemplate = function(templateData) {
    if (!templateData) {
        return;
    }

    // If not ready, not apply only at the first time.
    // So ready to apply after first time.
    if (this.readyDescription) {
        this.applyDescription(templateData);
    } else {
        this.readyDescription = true;
    }
    if (this.readyCustomfields) {
        this.applyCustomfields(templateData);
    } else {
        this.readyCustomfields = true;
    }
}

/**
 * Apply the description template to the ticket.
 * 
 * @param Template
 *            data object of TicketExt.
 */
ticketext.TicketTemplate.prototype.applyDescription = function(templateData) {
    // change description value
    var descElem = document.getElementById(this.descId);
    if (!descElem) {
        return;
    }
    
    var templateValue = templateData.template;
    
    // apply template
    var func = function() {
        descElem.value = templateValue;
    }
    
    this.execFunctionWithTracWysiwygPlugin(func);
}

/**
 * Apply the custom fields template to the ticket.
 * 
 * @param Template
 *            data object of TicketExt.
 */
ticketext.TicketTemplate.prototype.applyCustomfields = function(templateData) {
    
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
 * @param enablePropArray
 *            Enable property array
 */
ticketext.TicketTemplate.prototype.applyCustomfieldsForAdmin = function(enablePropArray) {
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
 * @param enablePropArray
 *            Enable property array.
 */
ticketext.TicketTemplate.prototype.applyCustomfieldsForTicket = function(enablePropArray) { 
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
        var elemName = inputElemArray[index].name;
        
        // include input fields.
        // exclude TracWysiwygPlugin fields.
        if (inputType.match("(text)|(checkbox)|(radio)|(file)")
         && elemName.indexOf(this.WYSISYG_EDITOR_PREFIX) != 0) {
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
 * Set element Id.
 * 
 * @param typeId
 *            The ticket type element id.
 * @param descId
 *            The ticket description element id.
 */
ticketext.TicketTemplate.prototype.setElementId = function(typeId, descId) {
    this.typeId = typeId;
    this.descId = descId;
}

/**
 * Apply the description on load page.
 * 
 * @param readyDescription
 *            if true, apply the description on load
 */
ticketext.TicketTemplate.prototype.setReadyDescription = function(readyDescription) {
    this.readyDescription = readyDescription;
}

/**
 * Apply the custom fields on load page.
 * 
 * @param readyCustomfields
 *            if true, apply the custom fields on load
 */
ticketext.TicketTemplate.prototype.setReadyCustomfields = function(readyCustomfields) {
    this.readyCustomfields = readyCustomfields;
}

/**
 * 
 * This function is needed for TracWysiwygPlugin. 
 * 
 * @param func
 *            execute function
 */
ticketext.TicketTemplate.prototype.execFunctionWithTracWysiwygPlugin = function(func) {
    if (typeof TracWysiwyg != "function" && typeof func != "function") {
        return;
    }
    
    // if TracWysiwygPlugin is used,
    // it must be chnage edit mode before change the description value.
    
    var editorMode;
    var txtareaModeElemArray = new Array();
    var wysiwygModeElemArray = new Array();
    
    for (var index = 0; index < this.WYSISYG_MAX_NUM; index++) {
        var countStr = String(index + 1);
        var txtareaModeElem = document.getElementById("editor-textarea-" + countStr);
        var wysiwygModeElem = document.getElementById("editor-wysiwyg-" + countStr);
        if (txtareaModeElem && wysiwygModeElem) {
            txtareaModeElemArray.push(txtareaModeElem);
            wysiwygModeElemArray.push(wysiwygModeElem);
        } else {
            break;
        }
    }
    
    editorMode = TracWysiwyg.getEditorMode();
    
    // change the editor mode.
    if (editorMode != "textarea") {
        for (var index = 0; index < txtareaModeElemArray.length; index++) {
            var txtareaModeElem = txtareaModeElemArray[index];
            if (txtareaModeElem) {
                txtareaModeElem.click();
            }
        }
    }
    
    // execute function.
    func();
    
    // revert the editor mode.
    switch (editorMode) {
    case "textarea":
        for (var index = 0; index < txtareaModeElemArray.length; index++) {
            var txtareaModeElem = txtareaModeElemArray[index];
            if (txtareaModeElem) {
                txtareaModeElem.click();
            }
        }
        break;
    case "wysiwyg":
        for (var index = 0; index < wysiwygModeElemArray.length; index++) {
            var wysiwygModeElem = wysiwygModeElemArray[index];
            if (wysiwygModeElem) {
                wysiwygModeElem.click();
            }
        }
        break;
    default:
       break;
    }
}

/**
 * Initialize TicketTemplate as static.
 * 
 * @param baseUrl
 *            The base URL of the ajax request.
 */
ticketext.TicketTemplate.setUp = function(baseUrl) {
    var ticketTemplateObj = new ticketext.TicketTemplate(baseUrl);
    ticketTemplateObj.initialize();
};
