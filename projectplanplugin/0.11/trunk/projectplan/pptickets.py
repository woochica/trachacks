# -*- coding: utf-8 -*-

import datetime
import pputil
from trac.util.datefmt import to_datetime, utc, to_utimestamp
from trac.ticket.model import Ticket
from ppenv import PPConfiguration
from ppenv import PPDateFormatOption

class TSExtensionRegister(object):
  '''
    TicketSet Extension Register
  '''
  # TODO: Class for Render/TicketSet Extension, with Documentation such that
  # Documentation can be generated for the Macro (Trac WikiMacro Listing)
  __r = {}

  @classmethod
  def add(cls,registrantcls,registername):
    '''
      Add a TSExtension:Name pair into the Register
    '''
    cls.__r[ registername ] = registrantcls

  @classmethod
  def keys(cls):
    '''
      Enumerate the Names
    '''
    return cls.__r.keys()

  @classmethod
  def get(cls,registername):
    '''
      Get the Matching Extension for a given Name
    '''
    return cls.__r[ registername ]

class ppTicket():
  '''
    Project Plan Ticket Class for extended Ticket Attributes
  '''
  def __init__(self,dataref,ticketset):
    '''
      initialize ticket object with data reference (dict with stored ticket data) and
      ticketset (ppTicketSet object which holds this object)
    '''
    self.__dataref = dataref
    self.__extensions = dict()

  def hasfield(self,name):
    '''
      check wether ticketdata has a key <name>
    '''
    return name in self.__dataref

  def getfield(self,name):
    '''
      return ticketdata for key <name>
    '''
    return self.__dataref[ name ]

  def getfielddefs( self ):
    '''
      return the set of valid fields
    '''
    #return self.__dataref.keys()
    return TicketSet.getfielddefs()

  def getfielddef(self,name,defval):
    '''
      return ticketdata for key <name> or default if theres no data
    '''
    if self.hasfield(name) and self.getfield(name):
      return self.__dataref[ name ]
    else:
      return defval

  def hasextension(self,name):
    '''
      check wether ticket extension with key <name> exists
    '''
    return name in self.__extensions

  def getextension(self,name,defaultvalue=None):
    '''
      return ticket extension for key <name> or None
    '''
    if self.hasextension( name ):
      return self.__extensions[ name ]
    else:
      return defaultvalue

  def _setextension(self,name,data):
    '''
      set an extension field
    '''
    self.__extensions[ name ] = data

  def _delextension(self,name):
    '''
      delete an extension field (which is f.e. temporary used for an extension)
    '''
    del self.__extensions[ name ]

  def get_changelog( self ):
    t = Ticket(self.env, id)
    return( t.get_changelog() )
  
  def getID( self ):
    self.getfield('id')
  
  def getstatus( self ):
    '''
      return status of ticket
    '''
    return self.getfield('status')
  
  def getpriority( self ) :
    '''
      return priority of ticket
    '''
    return self.getfield('priority')
 

class ppTicketSet():

  def __init__(self, macroenv):
    '''
      Initialize the ppTicketSet
    '''
    self.__extensions = dict()
    self.macroenv = macroenv
    self.__tickets = dict()

  def addTicket(self,ticket):
    '''
      add a new ticket with ticket data <ticket>
    '''
    #self.macroenv.tracenv.log.debug('addTicket: '+repr(ticket) )
    self.__tickets[ ticket['id'] ] = ppTicket(ticket,self)

  def deleteTicket(self,ticket):
    '''
      remove a new ticket with ticket data <ticket>
    '''
    self.deleteTicketId(ticket['id'])

  def deleteTicketId(self, tid):
    try:
      del self.__tickets[ tid ]
    except:
      pass

  @classmethod
  def getfielddefs( self ):
    return [ f['name'] for f in TicketSystem( self.macroenv.tracenv ).get_ticket_fields() ]

  def getIDList(self):
    '''
      return a list of ticket ids of tickets in this set
    '''
    return self.__tickets.keys();

  def getIDSortedList(self):
    '''
      return a  sorted list of ticket ids of tickets in this set
    '''
    idlist = self.__tickets.keys();
    idlist.sort()
    return idlist

  def getTicket(self,id):
    '''
      return the ppTicket object for a ticket with id <id>
    '''
    try:
      return self.__tickets[ id ]
    except KeyError:
      raise Exception('ticket not available: #%s (maybe increase the value of max_ticket_number_at_filters)' % (id,))

  def hasExtension(self,name):
    '''
      check wether ticketset extension with key <name> exists
    '''
    return name in self.__extensions

  def getExtension(self,name,defaultvalue=None):
    '''
      return ticketset extension for key <name> or None
    '''
    if self.hasExtension( name ):
      return self.__extensions[ name ]
    else:
      return defaultvalue

  def needExtension(self,name):
    '''
      execute an extension on this ticketset
    '''
    if self.hasExtension( name ):
      return
    else:
      if name in TSExtensionRegister.keys():
        extcls = TSExtensionRegister.get( name )
        if (extcls!=None):
          extensiono = extcls( self, self.__tickets )
          if (extensiono!=None):
            exttsdata = extensiono.extend()
            self.__extensions[ name ] = exttsdata
            return
      raise TracError( 'extension "%s" went missing or failed' % name )

  def get_changelog( self , ticketid):
    t = Ticket(self.macroenv.tracenv, ticketid)
    try: 
      return( t.get_changelog() )
    except:
      self.macroenv.tracenv.log.warning("get_changelog failed on ticket %s", ticketid)
      return [] # no changelogs


class ppTicketSetExtension():
  '''
    Base Class for TicketSet Extensions
  '''

  def __init__(self,ticketset,ticketsetdata):
    pass

  def extend(self):
    '''
      Execute the Extension and Extend Tickets and/or TicketSet with
      Extension fields. Return anything except None to Mark this extension
      as Executed. The Value will be put in the matching extension field for
      this Extension.
    '''
    return True

TSExtensionRegister.add( ppTicketSetExtension, 'base' )

class ppTSLastChange( ppTicketSetExtension ):
  '''
    Get the Last Ticket Changetime
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Check for all Changetimes and Return the highest Changetime as
      Int
    '''
    timemax = to_datetime( 0, utc )
    timenow = to_datetime( datetime.datetime.now(utc) )
    for k in self.__ts:
      v = self.__ts[ k ]
      ticketdt = to_datetime( v.getfielddef( 'changetime', timenow ) )
      if ticketdt > timemax:
        timemax = ticketdt
        if timemax == timenow:
          break
    return timemax

TSExtensionRegister.add( ppTSLastChange, 'tslastchange' )

class ppTSSetOfField( ppTicketSetExtension ):
  '''
    Generate a Set (List of non-duplicate Values), for
    a given Field.
  '''

  FieldName = ''
  DefValue = ''

  def __init__(self,ticketset,ticketsetdata):
    '''
      Get the Ticketdata
    '''
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Put all Values into a Set and Sort it.
      Return the Sorted Set for values of the given field.
    '''
    vset = set()
    for k in self.__ts:
      vset.add( self.__ts[ k ].getfielddef( self.FieldName, self.DefValue ) )
    return sorted( vset )

class ppTSVersions( ppTSSetOfField ):
  '''
    Generate a Sorted Set for the Version field
  '''

  FieldName = 'version'

TSExtensionRegister.add( ppTSVersions, 'tsversions' )

class ppTSMilestones( ppTSSetOfField ):
  '''
  Generate a Sorted Set for the Milestone field
  '''

  FieldName = 'milestone'

TSExtensionRegister.add( ppTSMilestones, 'tsmilestones' )

class ppTSDependencies( ppTicketSetExtension ):
  '''
    Generate a Dependency List which holds ppTicket Instances for the
    current TicketSet and another List which holds IDs for those
    Dependencies, which cant be resolved. (either because the
    there is no Instance for this Ticket in the current TicketSet or the
    Ticket with the given ID does not exist)
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__tso = ticketset
    self.__ts = ticketsetdata

  def extend(self):
    '''
      Calculate the field dependencies, which holds ppTicket Instances
      and the field all_dependencies which holds all given Ticket IDs, written
      in the dependency field for the current Ticket.
    '''
    depfield = self.__tso.macroenv.conf.get( 'custom_dependency_field' )

    for k in self.__ts:
      v = self.__ts[ k ]
      tid = v.getfield('id')
      authname = self.__tso.macroenv.tracreq.authname
      #intset = pputil.ticketIDsFromString( v.getfielddef( depfield, '' ) )
      dataaccess = DataAccessDependencies(self.__tso.macroenv.tracenv,authname)
      intset =   pputil.ticketIDsFromString(dataaccess.getDependsOn( v.getfield('id') ) )
      
      v._setextension( 'all_dependencies', intset )
      depset = set()
      for d in intset:
        if d in self.__ts:
          depset.add( self.__ts[ d ] )
      v._setextension( 'dependencies', depset )
      
    return True

TSExtensionRegister.add( ppTSDependencies, 'dependencies' )

class ppTSReverseDependencies( ppTicketSetExtension ):
  '''
    Calculate the reverse Dependencies for the dependencies extension field.
    This is a list of ppTicket Instances. The reverse dependencies field
    is also depending on the given TicketSet. Tickets not in this set, cant be
    set as reverse dependencies!
  '''

  def __init__(self,ticketset,ticketsetdata):
    self.__tso = ticketset
    self.__ts = ticketsetdata
    ticketset.needExtension( 'dependencies' )

  def extend(self):
    '''
      calculate the reverse_dependencies field based on the dependencies field.
    '''
    
    for k in self.__ts:
      self.__ts[ k ]._setextension( 'reverse_dependencies', set() )
    # reverse dependency calculation
    for k in self.__ts:
      v = self.__ts[ k ]
      tid = v.getfield('id')
      
      for d in v.getextension( 'dependencies' ):
        d.getextension( 'reverse_dependencies' ).add( v )
    return True

TSExtensionRegister.add( ppTSReverseDependencies, 'reverse_dependencies' )

class ppTSDueTimes( ppTicketSetExtension ):
  '''
    Calculate the time values.
    First, convert the given Text for Assign/Close Time into DateTime Values.
    Second, calculate Worktime / Assigndelay / Closingdelay without
    accessing the Database.
    Third, calculate Start and Finish Dates.
  '''

  def __init__(self,ticketset,ticketsetdata):
    '''
      Initialize with ticketset, ticketdata and calculate dependencies
    '''
    self.__tso = ticketset
    self.__ts = ticketsetdata
    if not ticketset.needExtension( 'dependencies' ):
      self = None

  def fieldtodatetime(self,v,field,dtf):
    '''
      convert a field, with given day/month/year mask into
      a datetime value
    '''
    
    theDate = v.getfielddef( field, 'DD/MM/YYYY' )
    if theDate != '' and not theDate.upper() in PPDateFormatOption.selectable() :
      AtheDate = None
      if dtf == 'DD/MM/YYYY':
        AtheDate = theDate.split('/');
        day_key = 0;
        month_key = 1;
        year_key = 2;
      if dtf == 'MM/DD/YYYY':
        AtheDate = theDate.split('/');
        month_key = 0;
        day_key = 1;
        year_key = 2;
      if dtf == 'DD.MM.YYYY':
        AtheDate = theDate.split('.');
        day_key = 0;
        month_key = 1;
        year_key = 2;
      if dtf == 'YYYY-MM-DD':
        AtheDate = theDate.split('-');
        year_key = 0;
        month_key = 1;
        day_key = 2;

      try:
        if AtheDate and len(AtheDate) == 3:
          year=int(AtheDate[year_key]);
          month=int(AtheDate[month_key]);
          day=int(AtheDate[day_key]);
          #return datetime.datetime(year,month,day)
          return datetime.date(year,month,day) # catch 64 bit problem
      except:
        # a problem appears, while parsing the date field
        # TODO: raise error message
        pass

    return None

  def extend(self):
    '''
      Calculate Datetime Values for Assign and Closing Time,
      calculate the difference to the current time in days and attach
      them into assigndiff and closingdiff extension fields for each ticket.
      Calculate the Workload (closing-assigntime) or set a Defaultworkload.
      Calculate start and finish Dates for each ticket, where both are
      either depending on the assign and closing time when it is on time or
      calculate start/finish date from now, such that workload is always the same,
      but start and finish are moving on overdue.

      no time is calculated, when both assign and close time are not given.
      (there is no dependency usage in the time calculation)
    '''
    adatefield = self.__tso.macroenv.conf.get( 'custom_due_assign_field' )
    cdatefield = self.__tso.macroenv.conf.get( 'custom_due_close_field' )
    adateformat = self.__tso.macroenv.conf.get( 'ticketassignedf' )
    cdateformat = self.__tso.macroenv.conf.get( 'ticketclosedf' )
    #dateNow = datetime.datetime.today()
    dateNow = datetime.date.today() # catch 64 bit problems

    for k in self.__ts:
      v = self.__ts[ k ]
      # set datetime values for assign/close - those can be None!
      adateTicket = self.fieldtodatetime( v, adatefield, adateformat )
      cdateTicket = self.fieldtodatetime( v, cdatefield, cdateformat )
      # defaultvalue -> conf
      defworktime = 1
      if adateTicket:
        v._setextension( 'assigndiff', (dateNow - adateTicket ).days )
      if cdateTicket:
        v._setextension( 'closingdiff', (dateNow - cdateTicket ).days )
      if (cdateTicket!=None) and (adateTicket!=None):
        v._setextension( 'worktime', ( cdateTicket - adateTicket ).days )
      else:
        v._setextension( 'worktime', defworktime )
        ptimedelta = datetime.timedelta( days = defworktime )
        if (cdateTicket!=None) or (adateTicket!=None):
          if cdateTicket:
            adateTicket = cdateTicket - ptimedelta
          if adateTicket:
            cdateTicket = adateTicket + ptimedelta
          if ( not v.hasextension( 'assigndiff' ) ) or ( not v.hasextension( 'closingdiff' ) ):
            if v.hasextension( 'assigndiff' ):
              v._setextension( 'closingdiff', v.getextension( 'assigndiff' ) - defworktime )
            if v.hasextension( 'closingdiff' ):
              v._setextension( 'assigndiff', v.getextension( 'closingdiff' ) + defworktime )
      if (adateTicket!=None) and (cdateTicket!=None):
        ###### static workload calculation
        if ( v.getextension( 'assigndiff' ) > 0 ) or ( v.getextension( 'closingdiff' ) > 0 ):
          if v.getextension( 'assigndiff' ) > 0:
            ptimedelta = datetime.timedelta( days = v.getextension( 'assigndiff' ) )
            adateTicket = adateTicket + ptimedelta
            cdateTicket = cdateTicket + ptimedelta
          else:
            ptimedelta = datetime.timedelta( days = v.getextension( 'closingdiff' ) )
            cdateTicket = cdateTicket + ptimedelta
        ######
        v._setextension( 'startdate', adateTicket )
        v._setextension( 'finishdate', cdateTicket )

    return True

TSExtensionRegister.add( ppTSDueTimes, 'duetimediffs' )

# Berechnung fuer End und Start Ticket in die Kritische Pfadanalyse einfuegen
#  -- pseudotickets einfuegen
#  -- berechnung
#  -- pseudotickets wieder entfernen und dependencies/reversedependencies/start/ende in ticketset extension feldern speichern
#    das ermoeglicht es die abhaengigkeiten in den grapviz renderern nachtraeglich einzubauen
class ppTSCriticalPathSimple( ppTicketSetExtension ):

  BETickets_Begin = 999999
  BETickets_End = 1000000

  def __init__(self,ticketset,ticketsetdata):
    self.__ts = ticketsetdata
    self.ticketset = ticketset
    self.ticketset.needExtension( 'dependencies' )
    self.ticketset.needExtension( 'reverse_dependencies' )
    self.ticketset.needExtension( 'duetimediffs' )

  def _inject_start_end(self ):
    '''
      Add Pseudo Project Begin and End Tickets
        - Begin Ticket has the Time t1 of earliest Ticket or
          now if now < t1
        - End Ticket has the Time t2 of latest Ticket or
          now if t2 < now
    '''
    # get the starting tickets
    starts = set()
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'dependencies' )) <= 0:
        starts.add( self.__ts[ k ] )

    dateNow = datetime.datetime.today()
    # add the pseudo ticket
    dateStart = dateNow
    for t in starts:
      if t.hasextension( 'startdate' ) and (
           t.getextension( 'startdate' ) != None ) and (
           t.getextension( 'startdate' ) < dateStart ):
        dateStart = t.getextension( 'startdate' )
    if dateStart < dateNow:
      pseudostat = 'closed'
    else:
      pseudostat = 'new'
    pseudoticket = { 'id' : self.BETickets_Begin,
                     'status': pseudostat }
    self.ticketset.addTicket( pseudoticket )
    # add extensions to the new pseudo ticket
    ppstartticket = self.__ts[ self.BETickets_Begin ]
    ppstartticket._setextension( 'dependencies', set() )
    ppstartticket._setextension( 'reverse_dependencies', starts )
    ppstartticket._setextension( 'startdate', dateStart )
    ppstartticket._setextension( 'finishdate', dateStart )
    # fix dependencies for "old" starting tickets
    for t in starts:
      t.getextension( 'dependencies' ).add( ppstartticket )

    # reverse procedure for the end ticket
    ends = set()
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'reverse_dependencies' )) <= 0:
        ends.add( self.__ts[ k ] )
    # add the pseudo ticket
    dateEnd = dateNow
    for t in ends:
      if t.hasextension( 'finishdate' ) and (
           t.getextension( 'finishdate' ) != None ) and (
           t.getextension( 'finishdate' ) > dateEnd ):
        dateEnd = t.getextension( 'finishdate' )
    pseudostat = 'new'
    pseudoticket = { 'id' : self.BETickets_End,
                     'status': pseudostat }
    self.ticketset.addTicket( pseudoticket )
    # add extensions to the new pseudo ticket
    ppendticket = self.__ts[ self.BETickets_End ]
    ppendticket._setextension( 'dependencies', ends )
    ppendticket._setextension( 'reverse_dependencies', set() )
    ppendticket._setextension( 'startdate', dateEnd )
    ppendticket._setextension( 'finishdate', dateEnd )
    # fix dependencies for "old" starting tickets
    for t in ends:
      t.getextension( 'reverse_dependencies' ).add( ppendticket )

  def _cleanup_start_end(self ):
    # prepare results - because both start and end are critical and buffers
    # are set in inner Tickets, the usefull data is time/dependencies
    result = { 'starts': self.__ts[ self.BETickets_Begin ].getextension( 'reverse_dependencies' ),
               'startdate': self.__ts[ self.BETickets_Begin ].getextension( 'startdate' ),
               'ends': self.__ts[ self.BETickets_End ].getextension( 'dependencies' ),
               'enddate': self.__ts[ self.BETickets_End ].getextension( 'finishdate' ) }
    # remove reverse_dependencies from starttickets (just empty them, they where empty before!)
    for t in result[ 'starts' ]:
      t._setextension( 'dependencies', set() )
    # same for end tickets + cleanup the mindepbuffer extension field which references the nonexisting endticket
    for t in result[ 'ends' ]:
      t._setextension( 'reverse_dependencies', set() )
      if t.hasextension( 'mindepbuffers' ):
        t._setextension( 'mindepbuffers', [] )
    # remove the pseudo tickets
    del self.__ts[ self.BETickets_Begin ]
    del self.__ts[ self.BETickets_End ]

    return result

  def extend(self):
    betickets = "betickets" in self.ticketset.macroenv.macroargs
    if betickets:
      self._inject_start_end()
    # pass 1, check for start and finish dates
    for k in self.__ts:
      v = self.__ts[ k ]
      if (not v.hasextension( 'startdate' )) or (not v.hasextension( 'finishdate' )):
        if betickets:
          self._cleanup_start_end()
        return False
    # pass 2. get the first nodes for topological run
    queue = []
    for k in self.__ts:
      if len(self.__ts[ k ].getextension( 'dependencies' )) <= 0:
        queue.append( k )
    # pass 3. breadth first topological run, calculate buffer times per dependency
    while len(queue)>0:
      current = queue.pop(0)
      if not self.__ts[ current ].hasextension( 'depbuffers' ):
        deps = self.__ts[ current ].getextension( 'reverse_dependencies' )
        depbuffers = []
        for d in deps:
          if d.getfielddef( 'status', '' )!='closed':
            if self.__ts[ current ].getfielddef( 'status', '' )!='closed':
              depbuffer = ( d.getfield('id'), ( d.getextension( 'startdate' ) - self.__ts[ current ].getextension( 'finishdate' ) ).days )
            else:
              depbuffer = ( d.getfield('id'), ( d.getextension( 'startdate' ) - self.__ts[ current ].getextension( 'startdate' ) ).days )
          else:
            depbuffer = ( d.getfield('id'), 0 )
          depbuffers.append( depbuffer )
          queue.append( d.getfield('id') )
        self.__ts[ current ]._setextension( 'depbuffers', depbuffers )
    # pass 4. get the first nodes for reverse run
    queue = []
    for k in self.__ts:
      try:
        if len(self.__ts[ k ].getextension( 'depbuffers', None )) <= 0:
          queue.append( k )
      except Exception,e:
	#raise Exception("ppTSCriticalPathSimple: k=%s, ts[k]=%s, e=%s, depbuffers=%s" % (k,repr(self.__ts[ k ]),e,self.__ts[ k ].getextension( 'depbuffers' )))
	pass
    # pass 5. breadth first in reverse order, calculate the deps with min. cumulative buffers
    runtest = 0; # var for endless loop check (cyclic dependencies in graph)
    startnode_minbuffer = 36500
    while ( len(queue) > 0 ) and (runtest <= ( 3*len( queue ) ) ):
      current = queue.pop(0)

      if not self.__ts[ current ].hasextension( 'mindepbuffers' ):
        depbufs = self.__ts[ current ].getextension( 'depbuffers', None)
        depbufsresolved = True
        if depbufs != None:
	  for (k,buf) in depbufs:
	    if not self.__ts[ k ].hasextension( 'mindepbuffers' ):
	      depbufsresolved = False
	      break
	  if not depbufsresolved:
	    # dependend buffermins are not calculated, recycle the current node for later testing
	    queue.append( current )
	    runtest = runtest +1
	  else:
	    runtest = 0
	    for d in self.__ts[ current ].getextension( 'dependencies' ):
	      queue.append( d.getfield('id') )
	    mindepbuffers = []
	    if len(depbufs)>0:
	      minbuf = 36500
	      for (k,buf) in depbufs:
		cbuf = ( buf + self.__ts[ k ].getextension( 'buffer' ) )
		if cbuf < minbuf:
		  minbuf = cbuf
	      self.__ts[ current ]._setextension( 'buffer', minbuf )
	      if len(self.__ts[ current ].getextension( 'dependencies' )) <= 0:
		if minbuf < startnode_minbuffer:
		  startnode_minbuffer = minbuf
	      for (k,buf) in depbufs:
		cbuf = ( buf + self.__ts[ k ].getextension( 'buffer' ) )
		if cbuf <= minbuf:
		  mindepbuffers.append( k )
	    else:
	      self.__ts[ current ]._setextension( 'buffer', 0 )
	    self.__ts[ current ]._setextension( 'mindepbuffers', mindepbuffers )
      else:
        runtest = 0
    if len(queue) > 0:
      raise Exception( " Cyclic dependencies found, fix dependencies or remove critical path analysis " )
      #return False
    # pass 6. get the first nodes for min buffer pathes
    queue = []
    for k in self.__ts:
      if ( len(self.__ts[ k ].getextension( 'dependencies' )) <= 0 ) and ( self.__ts[ k ].getextension( 'buffer' ) <= startnode_minbuffer):
        queue.append( k )
    # pass 7. mark the critical path
    while len(queue) > 0:
      current = queue.pop(0)
      self.__ts[ current ]._setextension( 'critical', True )
      for d in self.__ts[ current ].getextension( 'mindepbuffers' ):
        queue.append( d )

    # cleanup depbuffers
    for k in self.__ts:
      if self.__ts[ k ].hasextension( 'depbuffers' ):
        self.__ts[ k ]._delextension( 'depbuffers' )

    if betickets:
      return self._cleanup_start_end()
    else:
      return True

TSExtensionRegister.add( ppTSCriticalPathSimple, 'criticalpath_simple' )









class DataAccessDependencies(object):
  '''
    data access wrapper
  '''
  useTable = None

  
  class DataAccessDependenciesAbstract(object):
    '''
      abstract class
    '''
    ticket_comments = None
    authname = None
    
    def useFastSavingChangesOptimization( self ):
      try:
        return PPConfiguration( self.env ).get('use_fast_save_changes')
      except Exception,e:
        self.env.log.warning("use_fast_save_changes: Exception %s" % (e,))
        return False
    
    def reset_postponed_ticket_comments( self ):
      self.ticket_comments = {} # reset
    
    def postpone_ticket_comment(self, ticket_id, comment):
      self.env.log.debug("postpone_ticket_comment: #%s: %s" % (ticket_id,comment))
      if not self.ticket_comments.has_key(ticket_id):
        self.ticket_comments[ticket_id] = []
      self.ticket_comments[ticket_id].append(comment)
      
    def savePostponedTicketComments( self ):
      flag = PPConfiguration( self.env ).get('enable_save_dependency_changes_to_ticket_comments')
      for tid in self.ticket_comments.keys():
        if flag:
          self.save_changes( tid, "Changed Dependencies:\n"+"\n".join(self.ticket_comments[tid]))
      self.reset_postponed_ticket_comments()
  
    def save_changes( self, ticked_id, comment ):
      self.env.log.debug("save_changes: #%s: %s" % (ticked_id, comment) )
      if not self.useFastSavingChangesOptimization():
        Ticket(self.env, ticked_id).save_changes(self.authname, "Changed Dependencies:\n"+"\n".join(self.ticket_comments[ticked_id]) ) # add comment to ticket --> SLOW
      else:
        when_ts = to_utimestamp(datetime.datetime.now(utc))
        # SQL tested on MySQL and SQLite
        sql = '''
          UPDATE ticket SET changetime=%s WHERE id=%s;
          INSERT INTO ticket_change(ticket,time,author,field,oldvalue,newvalue) 
          SELECT ticket,%s,'%s',field,MAX(CAST(oldvalue AS UNSIGNED))+1,"%s" FROM ticket_change WHERE ticket = %s and field="comment" GROUP BY field;
        ''' % (when_ts, ticked_id, when_ts, self.authname, comment, ticked_id)
        self.env.log.debug("save_changes SQL:\n%s" % (sql,))
        self.env.get_db_cnx().cursor().execute(sql) # execute, but no commit
  
  
  
  class DataAccessDependenciesInCustomFields(DataAccessDependenciesAbstract):
    '''
      legacy implementation of ticket dependencies
    '''
    field = None
    fieldrev = None

    def __init__(self, env):
      self.env = env
      self.authname = authname
      self.field = PPConfiguration( self.env ).get('custom_dependency_field')
      self.fieldrev = PPConfiguration( self.env ).get('custom_reverse_dependency_field')
      self.reset_postponed_ticket_comments()
    
    def getDependsOn( self, ticket_id ):
      # self.env.log.debug('DataAccessDependenciesInCustomFields.getDependsOn of #'+str(ticket_id)+': '+ repr(Ticket(self.env, int(ticket_id)).get_value_or_default(self.field).replace(ticket_id, "")))
      return Ticket(self.env, int(ticket_id)).get_value_or_default(self.field).replace(ticket_id, "")

    def getBlockedTickets(self, ticket_id):
      '''
	calculate blocking tickets of the given ticket
	returns list of ticket ids (as string)
	Note: This a very inconvenient and expensive way. If you consider performance issues, then switch to Mastertickets compatibility mode
      '''
      sqlconstraint = 'false'
      
      # TODO precondition: normalize dependencies field
      sqlconstraint += " OR value = \"%s\"" % (ticket_id,) # lonely value
      sqlconstraint += " OR value LIKE \"%% %s,%%\"" % (ticket_id,) # middle
      sqlconstraint += " OR value LIKE \"%% %s\"" % (ticket_id,) # left 
      sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
      
      #sqlconstraint += " OR value = \"#%s\"" % (ticket_id,) # lonely value
      #sqlconstraint += " OR value LIKE \"%% #%s %%\"" % (ticket_id,) # middle
      #sqlconstraint += " OR value LIKE \"%%,%s\"" % (ticket_id,) # left 
      #sqlconstraint += " OR value LIKE \"%s,%%\"" % (ticket_id,) # right
      
      # LIMIT for safety reasons
      sql = "SELECT ticket FROM ticket_custom WHERE name = \"%s\" AND ( %s ) LIMIT 250" % (self.field, sqlconstraint )
      self.env.log.debug("getBlockedTickets: SQL: " + repr(sql))
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute(sql)
      blocking_tickets = cursor.fetchall()
      ret = []
      for res in blocking_tickets:
	ret.append(str(res[0]))
      return ret

    def saveDependenciesToDatabase( self, ticket_id, newvalue):
      '''
	save new value to ticket custom
      '''
      sql = "UPDATE ticket_custom SET value = \"%s\" WHERE ticket = \"%s\" AND name = \"%s\" " % (newvalue, ticket_id, self.field )
      self.env.log.debug("saveDependenciesToDatabase: %s" % (sql,));
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute(sql)
      db.commit()

      
    def addBlockedTicket( self, ticket_id, blocked_ticket_id ):
      '''
	add ticket_id to dependencies of blocked_ticket_id
      '''
      try:
	blocked_ticket_depends_on_tickets = self.getDependsOn(blocked_ticket_id)
	blocked_ticket_depends_on_ticket_list = self.splitStringToTicketList(blocked_ticket_depends_on_tickets)
	if not ticket_id in blocked_ticket_depends_on_ticket_list:
	  blocked_ticket_depends_on_ticket_list.append(str(ticket_id))
	  newvalue = self.createNormalizedTicketString(blocked_ticket_depends_on_ticket_list)
	  self.env.log.debug('add: save to '+blocked_ticket_id+': '+repr(blocked_ticket_depends_on_tickets)+' --> '+repr(newvalue))
	  
	  self.saveDependenciesToDatabase( blocked_ticket_id, newvalue )
	  comment = 'changed "'+blocked_ticket_depends_on_tickets+'" to "'+newvalue+'" (add '+ticket_id+') initiated by #'+str(ticket_id)
	  self.postpone_ticket_comment(blocked_ticket_id, comment) 
	
	else:
	  self.env.log.debug('not added: '+blocked_ticket_id+': '+repr(blocked_ticket_depends_on_tickets) )
      except Exception,e:
	self.env.log.error('ticket #%s error while adding a blocked ticket: %s' % ( ticket_id, repr(e) ) )
      

    def removeBlockedTicket( self, ticket_id, old_blockedtid):
      '''
	remove ticket_id from the dependencies of old_blockedtid
      '''
      dependencies = self.getDependsOn(old_blockedtid)
      dependencies_list = self.splitStringToTicketList(dependencies)
      new_dependencies_list = [ t.strip() for t in dependencies_list if str(t).strip() != ticket_id ]
      new_dependencies = self.createNormalizedTicketString(new_dependencies_list)
      
      self.saveDependenciesToDatabase( old_blockedtid, new_dependencies )
      comment = 'changed "'+dependencies+'" to "'+new_dependencies+'" (remove '+str(ticket_id)+') initiated by #'+str(ticket_id) 
      try:
	#Ticket(self.env, old_blockedtid).save_changes(self.authname, comment ) # add comment to ticket
	self.postpone_ticket_comment(old_blockedtid, comment)
	self.env.log.error('consider #%s: change dependencies of #%s: %s --> %s' % (ticket_id, old_blockedtid, dependencies, new_dependencies) )
      except Exception,e:
	self.env.log.error('error while adding the comment "%s" to #%s: %s' % (comment,ticket_id,repr(e)) )

    #def postpone_ticket_comment( self, ticket_id, comment):
      #Ticket(self.env, ticket_id).save_changes(self.authname, comment) # add comment to ticket
	
    def addBlockingTicket( self, ticket_id, blocking_ticket_id ):
      '''
	not needed 
      '''
      pass 
    
    def removeBlockingTicket( self, ticket_id, blocking_ticket_id ):
      '''
	not needed 
      '''
      pass 
    
    def commit(self):
      pass
    
  class DataAccessDependenciesInExtraTable(DataAccessDependenciesAbstract):
    '''
      ticket dependencies access compatible with Mastertickets Trac hack
    '''
    blockingticket_colname = 'source'
    blockedticket_colname = 'dest'
    
    def __init__(self, env, authname):
      self.env = env
      self.authname = authname
      self.db = self.env.get_db_cnx()
      self.cursor = self.db.cursor()
      self.reset_postponed_ticket_comments()
    
    def getBlockedTickets(self, ticket_id):
      '''
	calculate blocked tickets of the given ticket
	returns list of ticket ids 
      '''
      ret = self.getTicketDependencies( [ticket_id], self.blockedticket_colname)
      self.env.log.debug("getBlockedTicketsFromTable: #%s -> tickets: %s" % (ticket_id, repr(ret)) )
      return ret

    def getBlockedTicketsRecursively(self, ticket_id):
      '''
	calculate blocked tickets of the given ticket RECURSIVELY
	returns list of ticket ids 
      '''
      ret = self.getTicketDependenciesRecursively( [ticket_id], self.blockedticket_colname)
      self.env.log.debug("getBlockedTicketsFromTable Recursively: #%s -> tickets: %s" % (ticket_id, repr(ret)) )
      return ret

    
    def getDependsOn( self, ticket_id ):
      '''
	calculate blocking tickets of the given ticket
	returns list of ticket ids (as string)
      '''
      ret = self.getTicketDependencies( [ticket_id], self.blockingticket_colname)
      ret = ', '.join(ret)
    
      return ret

    def getDependsOnRecursively( self, ticket_id ):
      '''
	calculate blocking tickets of the given ticket RECURSIVELY
	returns list of ticket ids (as string)
      '''
      return self.getTicketDependenciesRecursively( [ticket_id], self.blockingticket_colname)

    def getTicketDependencies( self, ticket_ids, result_col ):
      '''
	generalized implementation of fetching data from dependencies table
      '''
      if result_col == self.blockingticket_colname:
	where_col = self.blockedticket_colname
      else:
	where_col = self.blockingticket_colname
	
      where = " OR ".join(["(%s = %s)" % (where_col,ticket_id) for ticket_id in ticket_ids])
      sql = "SELECT %s FROM mastertickets WHERE %s LIMIT 250" % (result_col, where)
      self.env.log.debug("getTicketDependencies: SQL: #%s -> %s" % (ticket_id, repr(sql)) )
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      cursor.execute(sql)
      blocking_tickets = cursor.fetchall()
      ret = []
      for res in blocking_tickets:
	ret.append(str(res[0]))
      return ret

    def getTicketDependenciesRecursively(self, ticket_ids, result_col ):
      '''
	generalized implementation of fetching RECURSIVELY data from dependencies table
      '''
      if result_col == self.blockingticket_colname:
	where_col = self.blockedticket_colname
      else:
	where_col = self.blockingticket_colname
      result_ticket_ids = []
      new_ticket_ids = ticket_ids
      
      while len(new_ticket_ids) > 0:
        new_ticket_ids = self.getTicketDependencies( new_ticket_ids, result_col )
        # remove all elements already discovered to prevent infinite loops
        new_ticket_ids = [tid for tid in new_ticket_ids if (not tid in result_ticket_ids) and (not tid in ticket_ids)]
        result_ticket_ids.extend(new_ticket_ids)
      
      return result_ticket_ids

    def performTicketAction( self, tid_from, tid_to, sql, comment ):
      self.dbexecute(sql)
      self.postpone_ticket_comment( tid_from, comment) 
      self.postpone_ticket_comment( tid_to, comment)
      
    def addBlockedTicket( self, ticket_id, blocked_ticket_id ):
      '''
	add ticket_id --> blocked_ticket_id
      '''
      sql = "INSERT INTO mastertickets (%s,%s) VALUES (%s,%s) " % (self.blockingticket_colname, self.blockedticket_colname, ticket_id, blocked_ticket_id )
      comment = '|| added||  #%s -> #%s  ||i.e., #%s is now blocked by #%s ||' % (ticket_id,blocked_ticket_id, blocked_ticket_id, ticket_id)
      self.performTicketAction( ticket_id, blocked_ticket_id, sql, comment )
    
    def removeBlockedTicket( self, ticket_id, old_blockedtid):
      '''
	remove ticket_id --> old_blockedtid
      '''
      sql = "DELETE FROM mastertickets WHERE %s = %s AND %s = %s " % (self.blockingticket_colname, ticket_id,  self.blockedticket_colname, old_blockedtid )
      comment = '|| removed||  #%s -> #%s  ||i.e., #%s is NOT blocked by #%s anymore ||' % (ticket_id,old_blockedtid, old_blockedtid,ticket_id)
      self.performTicketAction( ticket_id, old_blockedtid, sql, comment )
    
    def addBlockingTicket( self, ticket_id, blocking_ticket_id ):
      '''
	adapter
      '''
      self.addBlockedTicket( blocking_ticket_id, ticket_id )
    
    def removeBlockingTicket( self, ticket_id, blocking_ticket_id ):
      '''
	adapter
      '''
      self.removeBlockedTicket( blocking_ticket_id, ticket_id )

    def dbexecute( self, sql ):
      self.cursor.execute(sql)
    
    #def commit(self):
      #self.db.commit()
  
  
  def __init__(self, env, authname):
    self.env = env
    
    useTable = None
    try:
      useTable = PPConfiguration( self.env ).get('use_fast_save_changes');
    except Exception,e:
      useTable = False
    
    if useTable:
      self.dataaccess = DataAccessDependencies.DataAccessDependenciesInExtraTable(self.env, authname)
    else:
      # for legacy support
      self.dataaccess = DataAccessDependencies.DataAccessDependenciesInCustomFields(self.env)
    
  
  def getDependsOn( self, ticket_id ):
    '''
      calculate blocking tickets of the given ticket
      returns list of ticket ids (as string)
    '''
    return self.dataaccess.getDependsOn(ticket_id)

  def getBlockedTickets(self, ticket_id):
    '''
      calculate blocking tickets of the given ticket
      returns list of ticket ids (as string)
    '''
    return self.dataaccess.getBlockedTickets(ticket_id)

  def saveDependenciesToDatabase( self, ticket_id, newvalue):
    '''
      save new value to ticket
    '''
    self.dataaccess.saveDependenciesToDatabase( ticket_id, newvalue)

  def addBlockedTicket( self, ticket_id, blocked_ticket_id ):
    '''
      add ticket_id to dependencies of blocked_ticket_id
    '''
    self.dataaccess.addBlockedTicket( ticket_id, blocked_ticket_id )

  def removeBlockedTicket( self, ticket_id, old_blockedtid):
    '''
      remove ticket_id from the dependencies of old_blockedtid
    '''
    self.dataaccess.removeBlockedTicket( ticket_id, old_blockedtid)

  def addBlockingTicket( self, ticket_id, blocking_ticket_id ):
    '''
      add a ticket dependency
    '''
    self.dataaccess.addBlockingTicket( ticket_id, blocking_ticket_id )
  
  def removeBlockingTicket( self, ticket_id, blocking_ticket_id ):
    '''
      remove ticket dependency
    '''
    self.dataaccess.removeBlockingTicket( ticket_id, blocking_ticket_id )

  def commit(self):
    start = datetime.datetime.now()
    self.dataaccess.savePostponedTicketComments()
    try:
      self.env.get_db_cnx().commit() # commit all collected queries
    except Exception,e:
      self.env.log.warning("commit failed: %s " % (e,))
    self.env.log.debug("commit has taken %s sec" % (datetime.datetime.now() - start,))
    


    
