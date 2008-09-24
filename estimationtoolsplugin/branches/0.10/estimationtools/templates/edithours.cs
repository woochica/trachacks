 $(document).ready(function() {
    ids = $('td.id').each(function(i) {
       var id = $(this).text()
       var estimationField = '<?cs var:edithours.field ?>'
       $('td.' + estimationField + ' span').eq(i).editable(function(value, settings) {
         var currentElement = this;
         $.ajax({
           type: 'POST',
           url: 'xmlrpc',
           data: '<?xml version="1.0"?><methodCall><methodName>ticket.update</methodName>' +
        	   '<params><param><value><int>' + id + '</int></value></param>' +
        	   '<param><value><string></string></value></param>' +
        	   '<param><value><struct><member><name>' + estimationField + '</name>' +
        	   '<value><string>' + value + '</string></value></member></struct></value></param>' +
        	   '</params>  </methodCall>',
           contentType: 'text/xml',
           success: function(){
             $(currentElement).text(value);
           }
         });
         return('Saving...');
       }, {
	         tooltip   : 'Click to edit...',
	         placeholder: '',
	         onblur : 'submit',
	         select : 'true',
	         style : 'inherit',
	         width     : 60
       }); 
    });
 });