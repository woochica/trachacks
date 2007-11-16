/**
 * Search enhacement
 * 
 */
$(document).ready(function() {
	var resultChecks = document.getElementsByName('tr_search_result_userProfile');
	for(var i=0;i<resultChecks.length;i++){
		addEvent(resultChecks.item(i),'click',function(evt){ 
			if(evt)
				try{
					for(srcName in {'target':0,'srcElement':0}){
						if(evt[srcName]){	
							evt[srcName].parentNode.parentNode.className=evt[srcName].checked?"selected":"";
							break;
						}
					}
				}catch(Err){}
	    });
	}
});


/**
 * UserProfile inline update
 *
 */
function teamroster_notifyContainer(containerElement, srcElement){
	$(containerElement).addClass('editing');
	$(containerElement).find('.tr_userProfile_panel').css('display','block');	
	/*$(containerElement).find('input[@name=tr_userProfile_update]').css('visibility','visible');	
	$(containerElement).find('input[@name=tr_userProfile_cancel_update]').css('visibility','visible');	*/
}
	
$(document).ready(function(){
	$(".tr_editable")
		.each(function(){
			this.setAttribute("title", "Click to edit");
		});
	$(".tr_editable.text")
		.click(function(){
			if(this.innerHTML=='[blank]')this.innerHTML='';
			var newTextElement=document.createElement('INPUT');
			newTextElement.setAttribute('type','text');
			newTextElement.name=this.getAttribute('name');
			newTextElement.value=this.innerHTML;		
			this.parentNode.appendChild(newTextElement);	
	
			this.style.display='none';
			teamroster_notifyContainer($(this).parents('.tr_userProfile:first'), this);		
		});

	$(".tr_editable.textarea")
		.click(function(){
			if(this.innerHTML=='[blank]')this.innerHTML='';
			
			var newTextareaElement=document.createElement('TEXTAREA');
			newTextareaElement.name=this.getAttribute('name');		
			newTextareaElement.setAttribute('rows', this.getAttribute('rows'));
			newTextareaElement.setAttribute('cols', this.getAttribute('cols'));
		
			_htmlSource=$(this).find('.source').length>0?$(this).find('.source:first')[0].innerHTML:this.innerHTML;
		
			// Hack for IE6 which eats tab/CR/  innerHTML ...
			if(document.all)
				newTextareaElement.innerText=_htmlSource;
			else
				newTextareaElement.innerHTML= _htmlSource;

			this.parentNode.appendChild(document.createElement('BR'));
			this.parentNode.appendChild(newTextareaElement);				
			this.style.display='none';
			
			if(addWikiFormattingToolbar && $(this).is('.wikitext')){
				addWikiFormattingToolbar(newTextareaElement);
			}
			teamroster_notifyContainer($(this).parents('.tr_userProfile:first'), this);
		});

	$(".tr_editable.file")
		.click(function(){
			var newFileElement=document.createElement('INPUT');
			newFileElement.name=this.getAttribute('name');
			newFileElement.type="FILE";
			this.parentNode.appendChild(newFileElement);
			newFileElement.form.enctype="multipart/form-data";
			this.style.display='none';
			teamroster_notifyContainer($(this).parents('.tr_userProfile:first'), this);
		});

	$(".tr_editable.custom")
		.click(function(){
			if(this.innerHTML=='[blank]')this.innerHTML='';
			var newSpanElement=document.createElement('span');
			sourceElements=$(this).find('.source');
			if(sourceElements.length>0)
				newSpanElement.innerHTML=sourceElements[0].innerHTML;
				sourceElements[0].parentNode.removeChild(sourceElements[0]);
				
			this.parentNode.appendChild(newSpanElement);
	
			this.style.display='none';
			teamroster_notifyContainer($(this).parents('.tr_userProfile:first'), this);
		});

	$(".expander").click(function(){
		expandedElement = $('#'+this.getAttribute('for'))[0];
		if(!expandedElement)
			expandedElement = $(this).parents('tbody:first').find('div[@name='+this.getAttribute('for')+']')[0];		
		if(!expandedElement) return false;

		if($(this).is(".expander_open")){
			$(this).removeClass("expander_open");
			expandedElement.style.display='none';
		}else{
				$(this).addClass("expander_open");
				expandedElement.style.display='block';
			}

	});


});
