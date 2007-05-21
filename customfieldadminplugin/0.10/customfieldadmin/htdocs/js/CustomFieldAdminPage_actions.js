/**********
* User Interface function for Trac Custom Field Admin plugin.
* License: BSD
* (c) 2007      ::: www.Optaros.com (.....)
**********/

/**
* 
*/
function addcfType_validate( ){
    function getLabel( id ){
        var labelElements = document.getElementById('addcf').getElementsByTagName("LABEL");
        
        for( var i=0; i<labelElements.length; i++)  {
            if( labelElements[i].getAttribute("for") ==id )
                return labelElements[i];
        }
        
        return false;
    }
    
    function show( id ){
        try{
            document.getElementById( id ).style.display="block";
            if( label = getLabel(id))label.style.display="block";
        }catch(Err){}
    }
    
    function hide( id ){
        try{        
            document.getElementById( id ).style.display="none";
            if( label = getLabel(id))label.style.display="none";
        }catch(Err){}
    }
            
    switch(document.getElementById('type').selectedIndex){
        case 0:            
            hide('options');
            hide('cols');
            hide('rows');           
            break;
        case 1:
            show('options');
            hide('cols');
            hide('rows');               
            break;
        case 2:
            hide('options');
            hide('cols');
            hide('rows');               
            break;
        case 3:
            show('options');
            hide('cols');
            hide('rows');               
            break;
        case 4:
            hide('options');
            show('cols');
            show('rows');               
            break;
    }
        
}

/**
*
*/
addEvent(window,'load',function(){
    addcfType_validate();
    
    addEvent(document.getElementById('type'),'change',function(){
        addcfType_validate( );      
    });
});
