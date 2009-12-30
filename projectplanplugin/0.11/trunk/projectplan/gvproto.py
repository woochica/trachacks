# -*- coding: utf-8 -*-

import os

import ppenv

class NodePrototype():
  '''
    Node Prototype for Graphviz DOT Label HTML (a small and somewhat special
    subset of HTML)
  '''
  def __init__( self, macroenv ):
    '''
      Initialize an empty Node and the Tag stack
    '''
    self.macroenv = macroenv
    self.node = ''
    self.outrostack = []

  def _codeargs( self, **kwargs ):
    '''
      Write 'Argument="Value"' pairs into the Nodestring.
      This is for easy writing of Attributes from kwargs.
    '''
    nstring = ''
    for ( key, val ) in kwargs.items():
      nstring += '%s="%s" ' % ( key.upper(), val )
    return nstring

  def entertable( self, **kwargs ):
    '''
      Create an Opening TABLE Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<TABLE ' + self._codeargs( **kwargs ) + '>'
    else:
      self.node += '<TABLE>'
    self.outrostack.append( '</TABLE>' )

  def entertr( self ):
    '''
      Create an Opening TR (Tablerow) Tag and push the Closing Tag on stack.
    '''
    self.node += '<TR>'
    self.outrostack.append( '</TR>' )

  def entertd( self, **kwargs ):
    '''
      Create an Opening TD (Tablecell/column) Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<TD ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<TD>'
    self.outrostack.append( '</TD>' )

  def enterfont( self, color = "", face = "", size = "" ):
    '''
      Create an Opening FONT Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    self.node += '<FONT'
    if color != "":
       self.node += ' COLOR="%s"' % color
    if face != "":
       self.node += ' FACE="%s"' % face
    if size != "":
       self.node += ' POINT-SIZE="%s"' % size
    self.node += '>'
    self.outrostack.append( '</FONT>' )

  def enterimg( self, **kwargs ):
    '''
      Create an Opening IMG Tag, write the Attributes and
      push the Closing Tag on stack.
    '''
    if len( kwargs ) > 0:
      self.node += '<IMG ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<IMG>'
    self.outrostack.append( '</IMG>' )

  def enterbr( self, **kwargs ):
    '''
      Create an Opening BR (Linebreak) Tag and write the Attributes.
    '''
    if len( kwargs ) > 0:
      self.node += '<BR ' + self._codeargs( **kwargs ) + ' >'
    else:
      self.node += '<BR>'

  def leave( self, num = 1 ):
    '''
      Write num Closing Tags from Stack into the Nodestring.
    '''
    while num > 0:
      self.node += self.outrostack.pop()
      num -= 1

  def leaveall( self ):
    '''
      Write all Closing Tags from Stack into the Nodestring.
    '''
    self.leave( len( self.outrostack ) )

  def addmarkup( self, instr ):
    '''
      Write an arbitrary string into the Nodestring.
    '''
    self.node = self.node + instr + '\n'

  def render( self ):
    '''
      Return the Nodestring.
    '''
    return self.node

class TicketNodePrototype( NodePrototype ):
  '''
    Base Prototype for Ticket Nodes
    Creates HTML Code for GV Nodelabels
  '''

  def __init__( self, macroenv, ticket ):
    '''
      Initialize the Node Prototype and set usefull Vars.
    '''
    NodePrototype.__init__( self, macroenv )

    # get often used fields
    self.ticket = ticket
    self.ticketid = str( ticket.getfield( 'id' ) )
    self.tickettype = ticket.getfield( 'type' )
    self.ticketstatus = ticket.getfield( 'status' )
    self.ticketpriority = ticket.getfield( 'priority' )
    self.ticketuser = ticket.getfield( 'owner' )

    # get node color and image args
    self.fillcolor = self.macroenv.conf.get_map_val(
                       'ColorForStatus', self.ticketstatus )
    self.priocolor = self.macroenv.conf.get_map_val(
                       'ColorForPriority', self.ticketpriority )
    self.imgpath = ppenv.PPImageSelOption.absbasepath()

    # status image
    if self.macroenv.conf.get_map_val(
         'ImageForStatus', self.ticketstatus ) != 'none':
      self.statusim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val(
          'ImageForStatus', self.ticketstatus ) ) + '"></IMG>'
    else:
      self.statusim = self.ticketstatus

    # priority image
    if self.macroenv.conf.get_map_val(
         'ImageForPriority', self.ticketpriority ) != 'none':
      self.priorityim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get_map_val(
          'ImageForPriority', self.ticketpriority ) ) + '"></IMG>'
    else:
      self.priorityim = self.ticketpriority

    # user image (owner indicator)
    if self.ticketuser == self.macroenv.tracreq.authname:
      imgopt = 'ticket_owned_image'
      self.usercolor = self.macroenv.conf.get( 'ticket_owned_color' )
    else:
      imgopt = 'ticket_notowned_image'
      self.usercolor = self.macroenv.conf.get( 'ticket_notowned_color' )
    if self.macroenv.conf.get( imgopt ) != 'none':
      self.userim = '<IMG SRC="' + os.path.join( self.imgpath,
        self.macroenv.conf.get( imgopt ) ) + '"></IMG>'
    else:
      self.userim = self.ticketuser

    # set colwide for rows
    self.maxcolwide = 5

  def adddaterow( self ):
    '''
      Add a Daterow into the Node
    '''
    if self.ticketstatus == 'closed':
      # self.addmarkup( 'closed' )
      # save the line
      return

    self.entertr()
    self.entertd( title = "due",
                  href = "?ticket_inner?__dummy__",
                  bgcolor = "#FFFFFF",
                  colspan = str( self.maxcolwide ) )
    ticket_overdue_image = self.macroenv.conf.get( 'ticket_overdue_image' )

    if ( self.ticketstatus != 'closed' and
         self.ticket.hasextension( 'closingdiff' ) ):
      cd = self.ticket.getextension( 'closingdiff' )
      img = 'none'
      if cd > 0:
        bgcol = self.macroenv.conf.get( 'ticket_overdue_color' )
        img = os.path.join( self.imgpath, ticket_overdue_image)
        dueline = str( cd ) + ' days delayed'
      elif cd < 0:
        bgcol = self.macroenv.conf.get( 'ticket_ontime_color' )
        img = os.path.join( self.imgpath, ticket_overdue_image)
        dueline = str( 0 - cd ) + ' days left'
      else:
        bgcol = self.macroenv.conf.get( 'ticket_ontime_color' )
        img = os.path.join( self.imgpath, ticket_overdue_image)
        dueline = 'today'
      self.entertable( border = "0" )
      self.entertr()
      self.entertd( bgcolor = bgcol )
      if  ticket_overdue_image != 'none' and ticket_overdue_image != None:
        self.enterimg( src = img )
        self.leave( 2 )
      else:
        # fall back if no image is defined
        self.addmarkup( '<FONT COLOR="#FFFF00">!</FONT>' )
        self.leave( 1 )
      self.entertd()
      self.addmarkup( dueline )
      self.leave( 4 )
    else:
      self.addmarkup( 'due: unknown' )

    self.leave( 2 )

  def addstatuscol( self ):
    '''
      Add a Status Column into the Node
    '''
    href = '?ticket_state?%s?state=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketstatus )
    self.entertd( title = 'state', href = href,
                  color = '#F5F5F5', colspan = "1" )
    self.addmarkup( self.statusim )
    self.leave()
  
  def addconnectorcol( self ):
    '''
      Add a Status Column into the Node
    '''
    href = '?ticket_state?%s?state=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketstatus )
    self.entertd( title = 'connector', href = href,
                  color = '#F5F5F5', colspan = "1" )
    self.addmarkup( "X" )
    self.leave()

  def addprioritycol( self ):
    '''
      Add a Priority Column into the Node
    '''
    href = '?ticket_priority?%s?priority=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketpriority )
    self.entertd( title = 'priority', href = href,
                  color = '#F5F5F5', bgcolor = self.priocolor, colspan = "1" )
    self.addmarkup( self.priorityim )
    self.leave()

  def addownercol( self ):
    '''
      Add an Owner Column into the Node
    '''
    bgcol = self.usercolor
    href = '?ticket_owner?%s?owner=%s' % (
             self.macroenv.tracreq.href( 'query' ), self.ticketuser )
    self.entertd( title = self.ticketuser[ 0:10 ], bgcolor = bgcol,
                  href = href, color = '#F5F5F5', colspan = "1" )
    self.addmarkup( self.userim )
    self.leave()

  def addticketcol( self ):
    '''
      Add a Ticket Column into the Node
    '''
    self.entertd( title = "show ticket " + self.ticketid, color = "#F5F5F5",
                  colspan = "1",
                  href = "?ticket_inner?" + self.ticket.getfield( 'href' ) )
    self.addmarkup( self.ticketid )
    self.leave()

  def addsummaryrow( self ):
    '''
      Add a Summary Row into the Node
    '''
    self.entertr()
    self.entertd( TITLE = "summary", BGCOLOR = "#FFFFFF",
                  COLOR = "#F5F5F5", COLSPAN = str( self.maxcolwide ) )
    summary = self.ticket.getfield( 'summary' )
    if len( summary ) > 20:
      self.addmarkup( summary[ 0:16 ] + '...' )
    else:
      self.addmarkup( summary )
    self.leave( 2 )

  def adddebugtimes( self ):
    '''
      Add Debug Information for Critical Path Analyses (Estimated Start/Finish and Buffer)
    '''
    # 3 rows for tmp debug infos
    if self.ticket.hasextension( 'startdate' ):
      self.entertr()
      self.entertd( TITLE = "startdate", BGCOLOR = "#FFFFFF",
                    COLOR = "#F5F5F5", COLSPAN = str( self.maxcolwide ) )
      self.addmarkup( 'ETS %s ' % self.ticket.getextension(
                        'startdate' ).strftime( "%d/%m/%y" ) )
      self.leave( 2 )

    if self.ticket.hasextension( 'finishdate' ):
      self.entertr()
      self.entertd( TITLE = "finishdate", BGCOLOR = "#FFFFFF",
                    COLOR = "#F5F5F5", COLSPAN = str( self.maxcolwide ) )
      self.addmarkup( 'ETF %s ' % self.ticket.getextension(
                        'finishdate' ).strftime( "%d/%m/%y" ) )
      self.leave( 2 )

    if self.ticket.hasextension( 'buffer' ):
      self.entertr()
      self.entertd( TITLE = "buffer", BGCOLOR = "#FFFFFF",
                    COLOR = "#F5F5F5", COLSPAN = str( self.maxcolwide ) )
      self.addmarkup( "Buffer in Days: %s " % str(
                        self.ticket.getextension( 'buffer' ) ) )
      self.leave( 2 )

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    # table
    self.entertable( align = "CENTER", bgcolor = self.fillcolor, border = "1",
                     cellborder = "1", cellpadding = "1", cellspacing = "1",
                     color = "#C0C0C0", title = "Ticket: " + self.ticketid,
                     valign = "MIDDLE", href = "?ticket?__dummy__" )
    # first row, |ticketnumer|status|owner|priority|
    self.entertr()
    self.addticketcol()
    self.addstatuscol()
    self.addconnectorcol()
    self.addownercol()
    self.addprioritycol()
    self.leave()
    # second row, ticket description (first 22 chars of short description)
    self.addsummaryrow()
    #self.adddebugtimes()
    # add due row
    self.adddaterow()
    # finish
    self.leaveall()

    return NodePrototype.render( self )

class MilestoneNodePrototype( NodePrototype ):
  '''
    Base Prototype for Milestone Nodes
    Creates HTML Code for GV Nodelabels
  '''
  def __init__( self, macroenv, version, milestone, tickets, mtitlehref ):
    '''
      Initialize the Base Node Prototype.
    '''
    NodePrototype.__init__( self, macroenv )
    self.version = version
    self.milestone = milestone
    self.tickets = tickets
    self.href = mtitlehref

  def addtickettable( self ):
    '''
      Add a Table with Ticket per Due and per Status Information for this Milestone.
    '''
    statsmap = dict()
    delayedc = 0
    delayeda = 0
    intime = 0
    unknown = 0

    for t in self.tickets:
      s = t.getfielddef( 'status', '' )
      if s in statsmap:
        statsmap[ s ] += 1
      else:
        statsmap[ s ] = 1

      if s != 'closed':
        if t.hasextension( 'closingdiff' ) and (
             t.getextension( 'closingdiff' ) > 0 ):
          delayedc += 1
        elif t.hasextension( 'assigndiff' ) and (
               t.getextension( 'assigndiff' ) > 0 ):
          delayeda += 1
        else:
          if t.hasextension( 'closingdiff' ) and t.hasextension( 'assigndiff' ):
            intime += 1
          else:
            unknown += 1
      else:
        intime += 1

    if len( statsmap ) > 0:
      self.enterfont( color = '#000000', size = '10' )
      self.entertable( border = "0", cellborder = "1" )
      self.entertr()
      self.entertd( border = "0" )
      self.addmarkup( 'Tickets per Status' )
      self.leave( 2 )
      for ( key, val ) in statsmap.items():
        self.entertr()
        self.entertd( bgcolor = self.macroenv.conf.get_map_val(
                                  'ColorForStatus', key ) )
        if len( key ) > 0:
          self.addmarkup( key + ': ' + str( val ) )
        else:
          self.addmarkup( 'status unknown: ' + str( val ) )
        self.leave( 2 )
      if ( unknown > 0 ) or ( delayedc > 0 ) or ( delayeda > 0 ):
        self.entertr()
        self.entertd( border = "0" )
        self.addmarkup( 'Tickets per Due' )
        self.leave( 2 )
        def writeduecol( bgcol, text, num ):
          if num > 0:
            self.entertr()
            self.entertd( bgcolor = bgcol )
            self.addmarkup( text + ': ' + str( num ) )
            self.leave( 2 )
        writeduecol( '#FF0000', 'delayed closing', delayedc )
        writeduecol( '#FF0000', 'delayed assignment', delayeda )
        writeduecol( '#FFFF00', 'unknown', unknown )
        writeduecol( '#00FF00', 'on time', intime )
      self.leave( 2 )
    else:
      # that shouldn't ever happen, since gvrender/gvhierach only handles ms/ver with tickets
      self.entertr()
      self.entertd()
      self.addmarkup( 'no Tickets' )
      self.leave( 2 )

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    href = '?ticket?%s' % self.href
    self.enterfont( color = self.macroenv.conf.get( 'milestone_fontcolor' ),
                    size = '10' )
    self.entertable( align = "CENTER",
                     bgcolor = self.macroenv.conf.get( 'milestone_fillcolor' ),
                     border = "1", cellborder = "1",
                     color = self.macroenv.conf.get( 'milestone_color' ),
                     title = 'Milestone: %s' % self.milestone,
                     valign = "MIDDLE", href = href )
    self.entertr()
    self.entertd()
    self.addmarkup( '+ Milestone: ' + self.milestone )
    self.leave( 2 )
    self.entertr()
    self.entertd()
    self.addtickettable()
    self.leaveall()
    return NodePrototype.render( self )

class VersionNodePrototype( NodePrototype ):
  '''
    Base Prototype for Version Nodes
    Creates HTML Code for GV Nodelabels
  '''
  def __init__( self, macroenv, version, milestones, vtitlehref ):
    '''
      Initialize the Base Node Prototype.
    '''
    NodePrototype.__init__( self, macroenv )
    self.version = version
    self.milestones = milestones
    self.href = vtitlehref

  def addcompletiontable( self ):
    '''
      Create a Table with Completion Information for the Milestones in this
      Version.
    '''
    msmap = dict()
    for ( milestone, ticketlist ) in self.milestones.items():
      num = 0
      comp = 0
      for t in ticketlist:
        if t.getfielddef( 'status', '' ) == 'closed':
          comp += 1
        num += 1
      if num > 0:
        msmap[ milestone ] = '%s: %s%% [%s/%s]' % (
          milestone, str( ( comp * 100 ) / num ), str( comp ), str( num ) )
      else:
        msmap[ milestone ] = '%s: Empty' % milestone

    self.enterfont( color = '#000000', size = '10' )
    self.entertable( border = "0", cellborder = "1" )
    self.entertr()
    self.entertd( border = "0" )
    self.addmarkup( 'Milestone Completeness' )
    self.leave( 2 )
    for ( k, v ) in msmap.items():
      self.entertr()
      self.entertd()
      self.addmarkup( v )
      self.leave( 2 )
    self.leave( 2 )

  def render( self ):
    '''
      Create and Return the Node Markup
    '''
    href = '?ticket?%s' % self.href
    self.enterfont( color = self.macroenv.conf.get( 'version_fontcolor' ),
                    size = '11' )
    self.entertable( align = "CENTER",
                     bgcolor = self.macroenv.conf.get( 'version_fillcolor' ),
                     border = "1", cellborder = "1",
                     color = self.macroenv.conf.get( 'version_color' ),
                     title = 'Version: %s' % self.version,
                     valign = "MIDDLE", href = href )
    self.entertr()
    self.entertd()
    self.addmarkup( '+ Version: ' + self.version )
    self.leave( 2 )
    self.entertr()
    self.entertd()
    self.addcompletiontable()
    self.leaveall()
    return NodePrototype.render( self )

class GVRenderProto():
  '''
    Class which has some Methods for Node Prototype instantiation.
    Currently theres no special use for this but it can support
    different Node Prototypes for future settings. (f.e. using different
    Ticket Node Prototypes for different Priorities or something like that)
  '''

  @classmethod
  def ticket_gen_markup( cls, macroenv, ticket ):
    '''
      Create and Return Markup for the Ticket ticket
    '''
    return TicketNodePrototype( macroenv, ticket ).render()

  @classmethod
  def milestone_gen_markup( cls, macroenv, version,
                            milestone, tickets, mhref = None ):
    '''
      Create and Return Markup for the Milestone milestone in Version version and
      with Tickets tickets. mhref is a hypertext reference which should be used for
      the Milestone Table href (used for hierarchical renderer).
    '''
    return MilestoneNodePrototype( macroenv, version, milestone,
                                   tickets, mhref ).render()

  @classmethod
  def version_gen_markup( cls, macroenv, version, milestones, vhref = None ):
    '''
      Create and Return Markup for the Version version and its
      Milestones milestones. vhref is a hypertext reference which should be used for
      the Version Table href (used for hierarchical renderer).
    '''
    return VersionNodePrototype( macroenv, version, milestones, vhref ).render()
