# -*- coding: utf-8 -*-

from genshi.builder import tag

from trac.core import *
from trac.resource import *
from trac.ticket.query import *

from pptickets import *


class BaseFilter():
  '''
    Filter Superclass for Basic Filters
  '''

  # dont retrive the description, this is pure bloat
  IGNORE_FIELDS= [ u'description' ]

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter with Columns for Data retrival.
    '''
    self.macroenv = macroenv
    self.ticketset = {}
    self.cols = [ f['name'] for f in TicketSystem( self.macroenv.tracenv ).get_ticket_fields() ];
    for i in self.IGNORE_FIELDS:
      if i in self.cols:
        self.cols.remove( i )
    # transform ['col1','col2',...] list into "col=col1&col=col2&.." string
    self.colsstr = reduce( lambda x, y: x+'&'+y, map( lambda x: "col="+x, self.cols ) )

  def get_tickets( self ):
    '''
      Return a TicketSet.
      In this case it is Empty, since BaseFilter does Nothing.
    '''
    return self.ticketset

  def get_ticket_ids( self ):
    '''
      Return a List of Ticket Ids
      In this case it is Empty, since BaseFilter does Nothing.
    '''
    ticket_ids = []
    for t in self.get_tickets():
      ticket_ids.append(t['id'])
    return ticket_ids

class ParamFilter( BaseFilter ):
  '''
    Base Class for Filters that require a Parameter.
  '''
  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    BaseFilter.__init__( self, macroenv )
    self.queryarg = ""

  def set_queryarg( self, q ):
    '''
      Set the Parameter.
    '''
    self.queryarg = q

class NullFilter( BaseFilter ):
  '''
    Filter for "No Filtering", simply returns everything
  '''
  def get_tickets( self ):
    '''
      Return all Tickets using trac.ticket.query.Query
    '''
    return Query( self.macroenv.tracenv, order='id', cols=self.cols ).execute( self.macroenv.tracreq )

class QueryFilter( ParamFilter ):
  '''
    Class for Query Based Filters
  '''

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    ParamFilter.__init__( self, macroenv )
    self.filtercol = ""

  def set_col( self, c ):
    '''
      Set the Column for the Query.
      (The Query/Filter Parameter is passed to ParamFilter.set_queryarg)
    '''
    if self.filtercol in self.cols:
      self.cols.remove( self.filtercol )
    self.filtercol = c

  def get_tickets( self ):
    '''
      Query the Database and return
    '''
    if self.filtercol:
      self.macroenv.tracenv.log.debug('QueryFilter: %s=%s&%s' % ( self.filtercol, self.queryarg, self.colsstr ) )
      q = Query.from_string(self.macroenv.tracenv, '%s=%s&%s' % ( self.filtercol, self.queryarg, self.colsstr ) , order='id' )
      return q.execute( self.macroenv.tracreq )
    else:
      return NullFilter( self.macroenv ).get_tickets()

class AuthedOwnerFilter( QueryFilter ):
  '''
    Special Query Filter Class, which returns the Tickets for the currently
    authenticated Owner
  '''

  def __init__( self, macroenv ):
    '''
      Initialize and set QueryFilter args
    '''
    QueryFilter.__init__( self, macroenv )
    self.set_col( 'owner' )
    self.set_queryarg( self.macroenv.tracreq.authname )

class AuthedReporterFilter( QueryFilter ):
  '''
    Special Query Filter Class, which returns the Tickets for the currently
    authenticated Reporter
  '''

  def __init__( self, macroenv ):
    '''
      Initialize and set QueryFilter args
    '''
    QueryFilter.__init__( self, macroenv )
    self.set_col( 'reporter' )
    self.set_queryarg( self.macroenv.tracreq.authname )

class TicketBiDepGraphFilter( ParamFilter ):
  '''
    Special Query Filter Class, which returns the Tickets depending on
    self.queryarg (ticket id)
  '''
  cache = None

  DEPEXTENSION = ''

  def __init__( self, macroenv ):
    '''
      Initialize the Base Filter
    '''
    ParamFilter.__init__( self, macroenv )

  def get_tickets( self ):
    '''
      Query Database and Calculate Dependencies
    '''
    # get param
    v = self.queryarg
    self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: BEGIN %s  %s' % (self.DEPEXTENSION, v))
    # cached result values
    if self.cache != None:
      return self.cache 
    
    # query data
    ticketset = ppTicketSet( self.macroenv )
    ticketdata = NullFilter( self.macroenv ).get_tickets()
    for t in ticketdata:
      ticketset.addTicket(t)
    
    # calculate deps
    depqueue = list()
    depset = set()
    depqueue.append( int( v ) )
    depset.add( int( v ) )
    ticketset.needExtension( self.DEPEXTENSION )
    while len( depqueue ) > 0:
      #self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: depqueue: %s ' % (repr(depqueue)))
      current = depqueue.pop( 0 )
      cdata = ticketset.getTicket( current )
      deps = cdata.getextension( self.DEPEXTENSION )
      for d in deps:
        if int( d.getfield( 'id' ) ) not in depset:
          depqueue.append( int( d.getfield( 'id' ) ) )
          depset.add( int( d.getfield( 'id' ) ) )
    
    # build ticketlist with deps
    del ticketset
    depdata = list()
    for t in ticketdata:
      if int( t[ 'id' ] ) in depset:
         depdata.append( t )
    del ticketdata
    for t in depdata:
      self.macroenv.tracenv.log.debug('TicketBiDepGraphFilter: Result: %s' % (repr(t['id'])))
    
    self.cache = depdata # save calculated values
    return depdata

class TicketDepGraphFilter( TicketBiDepGraphFilter ):
  DEPEXTENSION = 'dependencies'


class TicketRevDepGraphFilter( TicketBiDepGraphFilter ):
  DEPEXTENSION = 'reverse_dependencies'


class ppFilter():
  '''
    Filter Director.
    Basic Class for usage of BaseFilter Filter. It checks for several
    Arguments and KW pairs in the given KW dict and Args List and Returns
    a ppTicketSet using the specified Filters.
  '''
  OPERATOR_AND = 'AND'
  OPERATOR_OR = 'OR'
  
  def __init__(self, macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def get_tickets(self):
    '''
      Build a ppTicketSet with Filters, specified in the Args List and
      KW Dict. On "notickets" Argument this will return an empty ppTicketSet,
      while no given Arguments and KW Paris will result in a complete ppTicketSet.
      This behavior and Filter execution can be change in this method.
    '''
    # skip queries, when 'notickets' arg is passed
    ticketset = ppTicketSet( self.macroenv )
    if 'notickets' in self.macroenv.macroargs:
      return ticketset

    filtered = False
    # entries: <kw key>: <query column>
    query_filters = {
      'filter_milestone': 'milestone',
      'filter_component': 'component',
      'filter_id':'id',
      'filter_type':'type',
      'filter_severity':'severity',
      'filter_priority':'priority',
      'filter_owner':'owner',
      'filter_reporter':'reporter',
      'filter_version':'version',
      'filter_status':'status',
      'filter_resolution':'resolution',
      'filter_keywords':'keywords'
    }

    # entries: <kw key>: <ParamFilter cls>
    # - value is passed with cls.set_queryarg, afterwards cls.get_tickets() is called
    param_filters = {
      'filter_ticketdeps': TicketDepGraphFilter,
      'filter_ticketrdeps': TicketRevDepGraphFilter
    }

    # entries: <args key>: <BaseFilter cls>
    # - only get_tickets() is called
    nullparam_filters = {
      'filter_owned': AuthedOwnerFilter,
      'filter_reported': AuthedReporterFilter
    }
    
    operator = self.macroenv.macrokw.get('combine_filters')
    
    # translate the keyword to a unified operator
    if operator != None:
      if operator.upper() in [ 'AND' , 'INTERSECT' ]:
        operator = self.OPERATOR_AND
      elif operator.upper() in [ 'OR' , 'UNION' ]:
        operator = self.OPERATOR_OR
      else:
        operator = None
    else: 
      # Fallback
      operator = self.OPERATOR_OR
    
    self.macroenv.tracenv.log.debug('combine_filters:'+str(operator))
    
    # add all tickets, if operator is AND
    if operator == self.OPERATOR_AND:
      ticketlist = NullFilter( self.macroenv ).get_tickets() #  AND, all tickets
      for t in ticketlist:
        ticketset.addTicket(t)
    #else:
      #ticketlist = NullFilter( self.macroenv ).get_tickets() # OR
    #self.macroenv.tracenv.log.error('pre-ticketset:'+repr(dir(ticketlist)))
    #self.macroenv.tracenv.log.error('pre-ticketset:'+repr(ticketlist))
    
    
    #ticketset = ppTicketSet() # OR
    # get tickets for "Parameter based Filters" using macrokw
    for ( k, v ) in self.macroenv.macrokw.items():
      filtered = False
      if k in query_filters:
        # get list of tickets
        self.macroenv.tracenv.log.debug('query_filters:'+repr(k))
        f = QueryFilter( self.macroenv )
        f.set_col( query_filters[ k ] )
        f.set_queryarg( v )
        filtered = True
        
      elif k in param_filters:
        self.macroenv.tracenv.log.debug('param_filters:'+repr(k))
        f = param_filters[ k ]( self.macroenv )
        f.set_queryarg( v )
        filtered = True
      
      if filtered:
        self.macroenv.tracenv.log.debug('currentTickets: '+repr(ticketset.getIDList()))
        # adapt ticket set
        if operator == self.OPERATOR_AND:
          self.macroenv.tracenv.log.debug('intersect allowedTickets: '+repr(f.get_tickets()))
          for tid in ticketset.getIDList():
            if not tid in f.get_ticket_ids(): # allowedTicketIDs
              ticketset.deleteTicketId( tid )
              #self.macroenv.tracenv.log.debug('remove ticket: '+str(tid))
        else: # OR
          for t in f.get_tickets():
            ticketset.addTicket( t )
    
    self.macroenv.tracenv.log.debug('result ids: ticketset:'+repr(ticketset.getIDList()))
    return ticketset



class ppFilterOld():
  '''
    Filter Director.
    Basic Class for usage of BaseFilter Filter. It checks for several
    Arguments and KW pairs in the given KW dict and Args List and Returns
    a ppTicketSet using the specified Filters.
  '''
  def __init__(self, macroenv):
    '''
      Initialize
    '''
    self.macroenv = macroenv

  def get_tickets(self):
    '''
      Build a ppTicketSet with Filters, specified in the Args List and
      KW Dict. On "notickets" Argument this will return an empty ppTicketSet,
      while no given Arguments and KW Paris will result in a complete ppTicketSet.
      This behavior and Filter execution can be change in this method.
    '''
    # skip queries, when 'notickets' arg is passed
    ticketset = ppTicketSet( self.macroenv )
    if 'notickets' in self.macroenv.macroargs:
      return ticketset

    filtered = False
    # entries: <kw key>: <query column>
    query_filters = {
      'filter_milestone': 'milestone',
      'filter_component': 'component',
      'filter_id':'id',
      'filter_type':'type',
      'filter_severity':'severity',
      'filter_priority':'priority',
      'filter_owner':'owner',
      'filter_reporter':'reporter',
      'filter_version':'version',
      'filter_status':'status',
      'filter_resolution':'resolution',
      'filter_keywords':'keywords'
    }

    # entries: <kw key>: <ParamFilter cls>
    # - value is passed with cls.set_queryarg, afterwards cls.get_tickets() is called
    param_filters = {
      'filter_ticketdeps': TicketDepGraphFilter,
      'filter_ticketrdeps': TicketRevDepGraphFilter
    }

    # entries: <args key>: <BaseFilter cls>
    # - only get_tickets() is called
    nullparam_filters = {
      'filter_owned': AuthedOwnerFilter,
      'filter_reported': AuthedReporterFilter
    }

    # get tickets for "Parameter based Filters" using macrokw
    for ( k, v ) in self.macroenv.macrokw.items():
      parmfilter = False
      self.macroenv.tracenv.log.error('Filter:'+repr(k))
      if k in query_filters:
        f = QueryFilter( self.macroenv )
        f.set_col( query_filters[ k ] )
        f.set_queryarg( v )
        parmfilter = True
      elif k in param_filters:
        f = param_filters[ k ]( self.macroenv )
        f.set_queryarg( v )
        parmfilter = True
      if parmfilter:
        ticketlist = f.get_tickets()
        # merge (OR like)
        for t in ticketlist:
          ticketset.addTicket( t )
        del ticketlist
        filtered = True

    # get tickets for "Null Parameter based Filters" using macroargs
    for k in self.macroenv.macroargs:
      if k in nullparam_filters:
        f = nullparam_filters[ k ]( self.macroenv )
        ticketlist = f.get_tickets()
        # merge
        for t in ticketlist:
          ticketset.addTicket( t )
        del ticketlist
        filtered = True

    # fallback to NullFilter, when nothin done
    if not filtered:
      ticketlist = NullFilter( self.macroenv ).get_tickets()
      for t in ticketlist:
        ticketset.addTicket(t)
      del ticketlist

    return ticketset
