# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter, IRequestFilter 
from trac.ticket.query import *
from ppenv import PPConfiguration
from ppenv import PPEnv
from pputil import *
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
import string
import re

class PPTicketDateTweak(Component):
  '''
    BETA: adds a javascript date picker to ticket view
  '''
  implements(IRequestFilter, ITemplateStreamFilter)
  """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""
  
  
  # IRequestFilter methods
  def pre_process_request(self, req, handler):
    return handler

  def post_process_request(self, req, template, data, content_type):
    """Do any post-processing the request might need; typically adding
      values to the template `data` dictionary, or changing template or
      mime type.
      
      `data` may be update in place.
      
        Always returns a tuple of (template, data, content_type), even if
        unchanged.
        
        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result
        
        (Since Trac 0.11)
        """
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      #add_script( req, 'projectplan/js/ticketdatepicker.js' )
      add_script( req, 'http://code.jquery.com/ui/1.10.3/jquery-ui.js' ) # load from CDN
      add_stylesheet( req, 'http://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css')
      add_script( req, 'projectplan/js/ticketdatepicker.js' )
    return template, data, content_type


  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      add the flag that indicates the activation of the date picker javascript
    '''
    if req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket'):
      macroenv = PPEnv( self.env, req, '' )
      # setting the values, s.t., they can be accessed by javascript code
      stream |= Transformer('body/div[@id="main"]').prepend(
        tag.div( 
          tag.div( macroenv.conf.get("custom_due_assign_field"), id='custom_due_assign_field_id' ) ,
          tag.div( self.env.config.get("ticket-custom", "%s.value" % (macroenv.conf.get( 'custom_due_assign_field'),) ), id='custom_due_assign_field_format' ) ,
          tag.div( macroenv.conf.get("custom_due_close_field"), id='custom_due_close_field_id' ) ,
          tag.div( self.env.config.get("ticket-custom", "%s.value" % (macroenv.conf.get( 'custom_due_close_field'),) ), id='custom_due_close_field_format' ) ,
          id='ppTicketViewTweakConf'
        )
      )
    
    return stream

