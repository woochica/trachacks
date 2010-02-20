# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import *
from genshi.builder import tag
from genshi.core import TEXT
from genshi.filters import Transformer
from genshi.input import HTML
from trac.ticket.api import ITicketManipulator
from trac.web.api import ITemplateStreamFilter # IRequestHandler, IRequestFilter, 
import re

class PPTicketViewTweak(Component):
  '''
    ALPHA STATE!
    computes links on ticket dependency entries
  '''
  implements(ITemplateStreamFilter)
  
  field = 'dependencies'

  # ITemplateStreamFilter methods
  def filter_stream(self, req, method, filename, stream, data):  
    '''
      replace the dependency-field by links
    '''
    
    #self.env.log.warn("ticket ="+str((data['ticket'].id))+" d="+str(data['ticket'].values.get('dependencies')) )
    try:
      dependencies = data['ticket'].values.get(self.field).strip()
      #dependencies = '1, 2 3;4' # test
      # TODO: replace this by a central method
      r = re.compile('[;, ]')
      deptickets = r.split(dependencies)
      
      depwithlinks = ''
      for dep in deptickets:
        # TODO: replace by absolute link
        if depwithlinks != '':
          sep = ', '
        else:
          sep = ''
        depwithlinks = tag.span(depwithlinks, sep, tag.a( dep, href="./"+dep, class_ = 'ticket' ) )
      
      stream |= Transformer('body/div[@id="main"]/div[@id="content"]/div[@id="ticket"]/table/tr/td[@headers="h_%s"]/text()' % self.field).replace(depwithlinks)
    except:
      pass
    
    return stream
 
 
 
 