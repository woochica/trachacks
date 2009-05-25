// from http://groups.google.com/group/jquery-en/browse_thread/thread/c43ee339e0b3960f/527c5ab71c2e92bc

jQuery.query = function(q) { 
         var r = {}; 
         q = q.replace(/^\?/,''); // remove the leading ? 
         q = q.replace(/\&$/,''); // remove the trailing & 
         jQuery.each(q.split('&'), function(){ 
                 var key = this.split('=')[0]; 
                 var val = this.split('=')[1]; 
                 // convert floats 
                 if(/^[0-9.]+$/.test(val)) 
                         val = parseFloat(val); 
                 // ingnore empty values 
                 if(val) 
                         r[key] = val; 
         }); 
         return r; 
}; 

// Call it like this: 
// q = $.query($(this).attr('href')); 
