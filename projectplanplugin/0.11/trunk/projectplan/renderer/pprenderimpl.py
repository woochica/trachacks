# -*- coding: utf-8 -*-


class RenderImpl():
  '''
    Renderer implementation baseclass
  '''
  FRAME_LABEL = 'Project Plan'

  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
  
  def getTitle(self):
    if self.macroenv.macrokw.get('title') != None:# title of the visualization
      #self.macroenv.tracenv.log.debug('title=%s' % (self.macroenv.macrokw.get('title'),))
      return self.macroenv.macrokw.get('title')
    else:
      return None

  
  def getHeadline( self ):
    '''
      overwrite the method 
      TODO: make abstract
    '''
    title = self.getTitle()
    if title != None:
      return('%s' % (title,))
    else:
      return('%s' % (self.FRAME_LABEL,))
  
  def log_warn( self, message ):
    '''
      shortcut: warn logging
    '''
    self.macroenv.tracenv.log.warn(message)

  def render(self, ticketset):
    '''
      Generate Output and Return XML/HTML Code/Tags suited for Genshi
    '''
    pass
    
    
