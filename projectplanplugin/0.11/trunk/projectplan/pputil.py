# -*- coding: utf-8 -*-

from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script


def addExternFiles(req):
  '''
    add javascript and style files
  '''
  # enable jquery tooltips
  add_script( req, 'projectplan/js/jquery-tooltip/lib/jquery.dimensions.js' )
  add_script( req, 'projectplan/js/jquery-tooltip/jquery.tooltip.js' )
  add_stylesheet( req, 'projectplan/js/jquery-tooltip/jquery.tooltip.css' )

  # move to gvrender?
  add_stylesheet( req, 'projectplan/css/projectplan.css' )
  add_script( req, 'projectplan/js/projectplan.js' )

 
def isNumber( string ) :
  '''
    checks if the given string is a number
  '''
  try:
    stripped = str(int(string))
    return True
  except:
    return False
