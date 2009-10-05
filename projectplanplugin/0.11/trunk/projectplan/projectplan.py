# -*- coding: utf-8 -*-

import re
import os
import os.path
import stat
import shutil
import datetime

from genshi.builder import tag

from trac.core import *
from trac.resource import *
from trac.attachment import Attachment
from trac.prefs.api import IPreferencePanelProvider
from trac.web import IRequestHandler
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.mimeview.api import get_mimetype
from trac.ticket.query import *
from trac.admin.api import *
from trac.perm import *

from ppfilter import *
from pptickets import *
from pprender import *
from ppenv import *

from pkg_resources import resource_filename

class PPConfigAdminPanel(Component):
    implements(IAdminPanelProvider)

    def get_admin_panels(self,req):
      """Return a list of available admin panels.

      The items returned by this function must be tuples of the form
      `(category, category_label, page, page_label)`.
      """
      if 'TRAC_ADMIN' in req.perm:
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'General', 'General Settings' )
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'Color', 'Color Settings' )
        yield( 'ProjectPlanConfig', 'ProjectPlan', 'Image', 'Image Settings' )

    def render_admin_panel(self, req, category, page, path_info):
      """Process a request for an admin panel.

      This function should return a tuple of the form `(template, data)`,
      where `template` is the name of the template to use and `data` is the
      data to be passed to the template.
      """
      req.perm.require( 'TRAC_ADMIN' )

      macroenv = PPEnv( self.env, req, '' )

      if req.method == 'POST':
        # ! evertime the configuration changes, wipe the Cache completly, since
        # most of the options change the rendering
        sexcept = ""
        try:
          macroenv.cache.wipe()
          self.env.log.info('cache %s wiped' % macroenv.cache.root )
        except Exception, e:
          self.env.log.exception(e)
        for k in macroenv.conf.flatconf.keys():
          if req.args.has_key( 'flat_' + k ):
            macroenv.conf.set( k, req.args[ 'flat_' + k ] )
        for ( k, optl ) in macroenv.conf.listconf.items():
          for subk in macroenv.conf.get_map( k ).keys():
            if req.args.has_key( 'list_' + k + '_' + subk ):
              macroenv.conf.set_map_val( k, subk, req.args[ 'list_' + k + '_' + subk ] )
        macroenv.conf.save()
        req.redirect( req.href.admin( category, page ) )

      if category == 'ProjectPlanConfig':
        confdict = self.__getconfdict( req, macroenv.conf, page )
        data = { 'confdict': confdict,
                 'page': page }
        return 'admin_ppconf.html',data
      else:
        raise TracError( "Unknown Category: %s" % category )

    def __getconfdict( self, req, conf, page ):
      confdict = {}
      # load flatconf with groupid and catid if existend
      for ( k, opt ) in conf.flatconf.items():
        if opt.groupid and opt.catid == page:
          if opt.groupid not in confdict:
            confdict[ opt.groupid ] = {}
          opttype = 'text'
          sellist = []
          chromebase = ''
          if isinstance( opt, PPSingleSelOption ):
            opttype = 'selectable'
            if isinstance( opt, PPImageSelOption ):
              opttype = 'selectable_image'
              chromebase = req.href.chrome( 'projectplan', opt.RelDocPath )
            s = opt.selectable()
            if isinstance( s, dict ):
              sellist = s.keys()
            elif isinstance( s, list ):
              sellist = s
            else:
              opttype = 'text'
              self.env.log.warning( 'Selectable for %s must be list or dict for html based selections, ignored.' % opt.key )
          confdict[ opt.groupid ][ opt.key ] = { 'opttype': opttype,
                                                 'val': conf.get( k ),
                                                 'id': 'flat_' + k,
                                                 'doc': opt.doc }
          if ( opttype=='selectable' ) or ( opttype=='selectable_image' ):
            confdict[ opt.groupid ][ opt.key ]['sellist'] = sellist
            if opttype=='selectable_image':
              confdict[ opt.groupid ][ opt.key ]['chromebase'] = chromebase

      # load listconf
      for ( k, optl ) in conf.listconf.items():
        if optl.groupid and optl.catid == page:
          opttype = 'text'
          sellist = []
          if isinstance( optl, PPListOfSelOptions ):
            opttype = 'selectable'
            if isinstance( optl, PPListOfImageSelOptions ):
              opttype = 'selectable_image'
              chromebase = req.href.chrome( 'projectplan', optl.selector().RelDocPath )
            s = optl.selector().selectable()
            if isinstance( s, dict ):
              sellist = s.keys()
            elif isinstance( s, list ):
              sellist = s
            else:
              opttype = 'text'
              self.env.log.warning( 'Selectable for %s must be list or dict for html based selections, ignored.' % optl.key )
          if optl.groupid not in confdict:
            confdict[ optl.groupid ] = {}
          for ( subk, subv ) in conf.get_map( k ).items():
            confdict[ optl.groupid ][ subk ] = { 'opttype': opttype,
                                                 'val': subv,
                                                 'doc': optl.doc % subk,
                                                 'id': 'list_' + k + '_' + subk }
            if ( opttype=='selectable' ) or ( opttype=='selectable_image' ):
              confdict[ optl.groupid ][ subk ]['sellist'] = sellist
              if opttype=='selectable_image':
                confdict[ optl.groupid ][ subk ]['chromebase'] = chromebase

      return confdict

class PPCacheContentProvider(Component):
    implements(IRequestHandler)

    # IRequestHandler methods
    def match_request( self, req ):
      '''
        match basicly everything, check later for existence
      '''
      return re.match( '/'+ PPConstant.cache_content_suffix + '/(.*)$', req.path_info )

    def process_request( self, req ):
      '''
        serve the request but check wether the file realy is in cache
        ( absolute second part, f.e. an attemp to access restricted areas )
        for those request, trying access files anywhere, serve an Exception,
        otherwise let let it handle send_file, which checks for existence and serves
        either the file or an error
      '''
      if req.path_info.startswith('/'):
        slashes = 2
      else:
        slashes = 1
      name = req.path_info[(slashes+len(PPConstant.cache_content_suffix)):]
      # dont use the cache, just verify the file existence and
      conf = PPConfiguration( self.env )
      cpath = os.path.normpath( conf.get( 'cachepath' ) )
      fname = os.path.normpath( name )
      if os.path.isabs( fname ):
        self.env.log.warn( 'Attempted bypass ( access for %s ) ' %fname )
        raise TracError( 'Access Denied for "%s"' % fname )
      accessname = os.path.join( cpath, name )
      # no isfile and exitence check, both are done on send_file with error handling
      return req.send_file( accessname, get_mimetype( accessname ) )


class ProjectPlanMacro(WikiMacroBase):
    '''
      Project Plan Macro
    '''
    implements(ITemplateProvider)

    def get_templates_dirs( self ):
      return [ resource_filename( __name__, 'templates' ) ]

    def get_htdocs_dirs( self ):
      return [ ( 'projectplan', resource_filename( __name__, 'htdocs' ) ) ]

    def expand_macro( self, formatter, name, content ):
        '''
          Wiki Macro Method which generates a Genshi Markup Stream
        '''
        macrostart = datetime.datetime.now()
        # verlagern in gvrender? -> stylesheet gehoert zu gvrender nicht direkt zum macro
        add_stylesheet( formatter.req, 'projectplan/css/projectplan.css' )
        macroenv = PPEnv( self.env, formatter.req, content )
        ts = ppFilter( macroenv ).get_tickets()
        return tag.div(
                 tag.div( tag.a( name=macroenv.macroid )( 'Projectplan '+macroenv.macroid  ) ),
                 ppRender().render( macroenv, ts ),
                 tag.div( str((datetime.datetime.now()-macrostart).microseconds/1000)+'ms' ) )
