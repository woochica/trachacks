# -*- coding: utf-8 -*-


class RenderImpl():
  '''
    Renderer implementation baseclass
  '''

  def __init__(self,macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv
  
  def getHeadline( self ):
    '''
      overwrite the method 
      TODO: make abstract
    '''
    return('Projectplan')
  
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
    
    
