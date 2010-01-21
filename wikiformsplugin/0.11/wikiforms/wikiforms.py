# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Verigy (Singapore) Pte. Ltd.
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#
from trac.core            import *
from trac.wiki.macros     import WikiMacroBase
from trac.wiki.formatter  import Formatter
from trac.env             import IEnvironmentSetupParticipant
from trac.web             import IRequestHandler
from trac.web.api         import HTTPBadRequest, HTTPUnauthorized
from datetime             import datetime, date, timedelta
from trac.util.datefmt    import format_datetime, utc, pretty_timedelta, timezone
from trac.perm            import PermissionSystem, IPermissionRequestor ,PermissionError
from trac.db.schema       import Table, Column

import sys
import StringIO
import re
import random
import traceback
import time

class WikiFormsMacro(WikiMacroBase,Component):
    implements(IEnvironmentSetupParticipant,IRequestHandler,IPermissionRequestor)

    """
       Docs for WikiForms wiki processor...
    """

    # ===========================================================================================================================
    # === Class Variables
    # ===========================================================================================================================

    # Database schema version (used to detect the need for upgrades)...
    db_version = 1

    # Database schema
    db_schema = [Table('wikiforms_fields',key=('field'))[					  
    							 Column('field' 		    ),      
    							 Column('value' 		    ),      
    							 Column('updated_by'		    ),      
    							 Column('updated_on', type='INTEGER')	    	  
    							]					    	  
    		]

    # currently installed database schema version is stored here...
    found_db_version = None;
    
    # 
    placeholder_cnt  = 0

    # ===========================================================================================================================
    # === extended Trac Extension Points...
    # ===========================================================================================================================

    # IPermissionRequestor methods
    def get_permission_actions(self):
      return ['WIKIFORMS_ADMIN', 'WIKIFORMS_UPDATE']

    # --------------------------------------------------------------------------------------------------------------------------

    # IEnvironmentSetupParticipant
    def environment_created(self):
        """
	   Called when a new Trac environment is created.
	"""
	
        WikiFormsMacro.found_db_version = 0
        self.upgrade_environment(self.env.get_db_cnx())
    
    # --------------------------------------------------------------------------------------------------------------------------

    def environment_needs_upgrade(self, db):
        """
	   Called when Trac checks whether the environment needs to be upgraded.
           Returns `True` if upgrade is needed, `False` otherwise.
	"""
  
        cursor = db.cursor()
        cursor.execute("SELECT value FROM system WHERE name='wikiforms_version'")
        value = cursor.fetchone()
        if not value:
            WikiFormsMacro.found_db_version = 0
            return True
        else:
            WikiFormsMacro.found_db_version = int(value[0])
            return WikiFormsMacro.found_db_version < WikiFormsMacro.db_version

    # --------------------------------------------------------------------------------------------------------------------------

    def upgrade_environment(self, db):
        """
	   Actually perform an environment upgrade, but don't commit as
           that is done by the common upgrade procedure when all plugins are done.
	"""

        from trac.db import DatabaseManager			      
        db_manager = DatabaseManager(self.env)._get_connector()[0] 

        # Insert the default table
        cursor = db.cursor()
	
        if not WikiFormsMacro.found_db_version:
	  # remember current database schema version...
          cursor.execute("INSERT INTO system (name, value) VALUES ('wikiforms_version', '%s')" % (WikiFormsMacro.db_version))
        else:
	  # remember current database schema version...
          cursor.execute("UPDATE      system SET value = %s WHERE name = 'wikiforms_version'"  % (WikiFormsMacro.db_version))  

          # in case tables (from previous versions) are already available, remove them...
          for tbl in WikiFormsMacro.db_schema:											  
            try:				      	  									
              cursor.execute('DROP TABLE %s' % tbl.name)      								
            except:				      	  									
              pass				      	        								

        # create tables according defined schema...
        for tbl in WikiFormsMacro.db_schema:
          for sql in db_manager.to_sql(tbl):  
            cursor.execute(sql)  	      

    # --------------------------------------------------------------------------------------------------------------------------

    def match_request(self, req):
        return req.path_info.endswith('/wikiforms/update')

    # --------------------------------------------------------------------------------------------------------------------------

    def process_request(self, req):
        """
	   Called when the user wants to save a form content.
	"""
        try:
	    # check whether user has form-update permissions...
	    msg = "You(%s) don't have enough permissions to update form values..." % (req.authname)
	    if (req.perm.has_permission('WIKIFORMS_UPDATE')
	    	or
		req.perm.has_permission('WIKIFORMS_ADMIN')):
	      pass
	    else:
	      raise TracError(msg)

            args = dict(req.args)
            #
            # you get something like this...
            #
	    #{
	    # '__BACKPATH'  : u'/trac/TPdev/wiki/sandbox', 
	    # '__FORM_TOKEN': u'28b12aa6e225d804bd863ec0', 
	    # '__SUBMIT'    : u'Commit', 
	    # '/wiki/sandbox/spec_comment': u'Please fill in your comment...', 
	    # '/wiki/sandbox/spec_completion': u'foo', 
	    # '/wiki/sandbox/spec_done': u'my_value', 
	    # '/wiki/sandbox/choose_one': u'val2', 
	    # '/wiki/sandbox/approval_comment': u'Please fill your\r\napproval\r\ncomment\r\nhere'
	    #}
            #
    	    #self.log.debug(req.args)
            backpath   = args.pop('__BACKPATH'  , None)
            form_token = args.pop('__FORM_TOKEN', None)
            submit     = args.pop('__SUBMIT'    , None)
            page       = args.pop('__PAGE'      , None)

            if page is None:
                raise HTTPBadRequest('__PAGE is required')

            fields_to_be_stored  = {}
	    fields_to_be_deleted = []
	    
            for name,value in args.iteritems():
	      if (re.match('/[0-9]+:[0-9]+/$',name)):
                # there is a checkbutton...
		if (value not in args):
		  # ...which is unchecked => remove database entry...
		  fields_to_be_deleted.append(value)
	      else:
	        fields_to_be_stored[name]=value  	    

            # store all values in database...
            db       = self.env.get_db_cnx()  
            authname = req.authname	      
            for name,value in fields_to_be_stored.iteritems():
	      value = re.sub('(\r\n|\r|\n)','\\\\n',value)
	      
              msg = self.set_tracform_field(db,name,value,authname)

            # remove obsolete fields (unchecked checkboxes)...
            for resolved_name in fields_to_be_deleted:
              msg = self.delete_tracform_field(db,resolved_name)
	      
	    # set form modification date...  
	    msg = self.set_tracform_field(db,page,'',authname)

            if backpath is not None:
                req.send_response(302)
                req.send_header('Content-type', 'text/plain')
                req.send_header('Location', backpath)
                req.end_headers()
                req.write('OK')
            else:
                req.send_response(200)
                req.send_header('Content-type', 'text/plain')
                req.end_headers()
                req.write('OK')
        except Exception, e:
            req.send_response(500)
            req.send_header('Content-type', 'text/plain')
            req.end_headers()
            req.write(str(e))

    # --------------------------------------------------------------------------------------------------------------------------

    def expand_macro(self, formatter, name, args):
        """
	   Called to build the form from the wiki-processor-content...
	"""
        # set defaults...
	page	= formatter.req.path_info   	 
        context = ''		            	 
        db      = formatter.env.get_db_cnx()										   
	
        # parse request...
	unprocessed = args		      
	result      = ''  			        							      
	#result    += '{{{\n' + unprocessed + '\n}}}\n'    							      

	final_html = {}
	  													      
        while (unprocessed != ''):
	  # search for start-of-tag...										      
	  start_tag = unprocessed.find('<tf>')									      
	  													      
	  if (start_tag >= 0):											      
	    # start-tag found...										      
	    # search for end-tag...										      
	    end_tag = unprocessed.find('</tf>',start_tag+1) 							      
	    													      
	    if (end_tag >= 0):											      
	      # start-tag and end-tag found...									      
	      result	    += unprocessed[0	     : start_tag  ]	# part before start-tag...
	      tag	     = unprocessed[start_tag+4 : end_tag  ]	# part between start- and end-tag...				      
	      full_tag	     = unprocessed[start_tag   : end_tag+5]	# part including start- and end-tag...				      
	      unprocessed    = unprocessed[end_tag  +5 :  	  ]	# part after end-tag...			      

              tag = re.sub('#[^\n\f]*','',tag) # strip comments...						      

              command,options = self.get_piece(tag)

              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              if (command=='context'):							      
        	# set context to...
		context,ignored = self.get_piece(options)
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='value'):							      
        	# get value of...
		name,ignored  = self.get_piece(options)
                resolved_name = self.resolve_name(page,context,name)	  

                db            = formatter.env.get_db_cnx()
		msg,entry     = self.get_tracform_field(db,resolved_name)    
        	result       += "%s" % entry['value']			  
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='values'):							      
        	# get value of...
		local_context,parameters = self.get_piece(options)
												      
		while (parameters!=''): 				    
		  m=re.match('(.*?)<(\S+?)>(.*)$',parameters)		    
		  if (m is not None):					    
		    result     += m.group(1)  				    
		    name	= m.group(2)  				    
		    parameters  = m.group(3)  				    

                    resolved_name = self.resolve_name(page,local_context,name)	    
                    db            = formatter.env.get_db_cnx()
		    msg,entry	  = self.get_tracform_field(db,resolved_name)  
          	    result	 += "%s" % entry['value']		    
		  else: 						    
		    result     += parameters				    
		    parameters  = ''  					    
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='who'):							      
        	# get updated_by of...										      
		name,ignored  = self.get_piece(options)

                resolved_name  = self.resolve_name(page,context,name)
                db             = formatter.env.get_db_cnx()
        	msg,entry      = self.get_tracform_field(db,resolved_name)					      
		result        += "%s" % entry['updated_by']								      
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='when'):							      
        	# get updated_on of...										      
		name,ignored = self.get_piece(options)

		resolved_name = self.resolve_name(page,context,name)
                db            = formatter.env.get_db_cnx()
        	msg,entry     = self.get_tracform_field(db,resolved_name)     	 			      
		result       += "%s" % self.to_timestring(entry['updated_on'])
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='lastmodified'):							      
        	# get updated_on,updated_by of...										      
		name,ignored = self.get_piece(options)

		resolved_name = self.resolve_name(page,context,name)
                db            = formatter.env.get_db_cnx()
        	msg,entry     = self.get_tracform_field(db,resolved_name)  				      

                now = datetime.now(utc)
						  
                if (entry['field'] is not None):
                  last_modified = datetime.fromtimestamp(entry['updated_on'], utc)
		  pretty_delta  = pretty_timedelta(now,last_modified)
                  timezone_name = formatter.req.session.get('tz')
                  if (timezone_name == None):
        	    timezone_name = "utc"
		  time_string   = format_datetime(last_modified,'%a %b %d %T %Y %Z',timezone(timezone_name))
		else:
                  time_string   = self.to_timestring(entry['updated_on'])
		  pretty_delta  = 'unset-time'

                result += "'''Last Modified:''' %s (%s ago) by %s" % (
                           time_string,
			   pretty_delta,      
			   entry['updated_by']
			  )
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='set'):							      
        	# set value of...										      
		name,value = self.get_piece(options)

                resolved_name = self.resolve_name(page,context,name)
		authname      = formatter.req.authname
                db            = formatter.env.get_db_cnx()
        	msg           = self.set_tracform_field(db,resolved_name,value,authname)				      
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='dump'):							      
        	# dump fields...										      
		name,ignored = self.get_piece(options)
                db           = formatter.env.get_db_cnx()
        	msg,rows     = self.get_tracform(db)									      
														      
		#result += "{{{\n" 				      
		result += "||'''field'''||'''value'''||'''who'''||'''when'''\n" 				      
		for row in rows:										      
		  m = re.search(name,row['field']);							      
		  if m: 											      
		    result += "||%s||%s||%s||%s\n" % (row['field'],
		                                      re.sub('\n','\\\\n',row['value']),
						      row['updated_by'],
						      row['updated_on'])  
		#result += "\n}}}" 				      
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='delete'):							      
        	# delete a field...	

		# check for WIKIFORMS_ADMIN permission...									      
  	        msg = "You(%s) don't have enough permissions to delete form values..." % (formatter.req.authname)
	        if (formatter.req.perm.has_permission('WIKIFORMS_ADMIN')):
		  pass
		else:
	          raise TracError(msg)
		
		
		name,ignored    = self.get_piece(options)
                resolved_name   = self.resolve_name(page,context,name)
                db              = formatter.env.get_db_cnx()
        	msg             = self.delete_tracform_field(db,resolved_name)				      
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='checkbox'):
        	# create checkbox...
		name,parameters  = self.get_piece(options)
		resolved_name    = self.resolve_name(page,context,name)
		
		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_checkbox(db,name,resolved_name,parameters,placeholder_id)			   					   
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='radio'):						      
        	# create radio...			        						   
		name,parameters  = self.get_piece(options)
		resolved_name    = self.resolve_name(page,context,name)

		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_radio(db,name,resolved_name,parameters,placeholder_id)			   					   
             # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='input'):						      
        	# create input...			        						   
		name,parameters  = self.get_piece(options)
		resolved_name    = self.resolve_name(page,context,name)

		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_input(db,name,resolved_name,parameters,placeholder_id)			   					   
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='textarea'):						      
        	# create text...			        						   
		name,parameters = self.get_piece(options)
		resolved_name   = self.resolve_name(page,context,name)

		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_textarea(db,name,resolved_name,parameters,placeholder_id)			   					   
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='select'):						      
        	# create select...			        						   
		name,parameters  = self.get_piece(options)
		resolved_name    = self.resolve_name(page,context,name)

		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_select(db,name,resolved_name,parameters,placeholder_id)			   					   
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 	      
              elif (command=='submit'):						      
        	# create button...
					        						   
		placeholder_id   = self.get_placeholder_id()
		result          += placeholder_id
		
        	final_html[placeholder_id] = self.create_submit(name,resolved_name,options,placeholder_id)			   					   
              # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
	      else:
	        # unknown command => echo original description including tags around...	      
		result += full_tag
	    else:												      
	      # start-tag but no end-tag found...								      
	      result	  += unprocessed	   									 
	      unprocessed  = ''       	   									 

	  else: 												      
	    # no start-tag found...										      
	    result	+= unprocessed    									     
	    unprocessed	 = '' 	        									     

        # wikify structure of document...
	result = self.wiki_to_html(formatter,result)
	
	# fill in final html for placeholders...
	for placeholder_id,placeholder_value in final_html.iteritems():
	  result = re.sub(placeholder_id,placeholder_value,result,1)

        return ''.join(self.build_form(formatter,page,result))

    # ===========================================================================================================================
    # === supporting functions...
    # ===========================================================================================================================

    def create_checkbox(self, db, name, resolved_name, parameters, placeholder_id):
        # create checkbox...
	result       = ''											   	   
	checkbox_def = {'cfg'   : {'name'    : resolved_name       ,						   	   
	              		   'checked' : False		   ,						   	   
	              		   'value'   : 'true'		   ,						   	   
	              		   'class'   : 'checkbox_css_class',						   	   
	              		   'id'      : 'checkbox_css_id'   ,						   	   
				   'debug'   : False								   	   
		                  },										   	   
	      	        'xtras' : [],										   	   
	      	        'xtra'  : {}										   	   
	      	       }											   	   

        # ...overwrite hardcoded defaults with user-defined values...						   	   
	checkbox_def = self.parse_options(parameters,checkbox_def)						   	   
														   	   
	# fetch state from database...										   	   
        msg,entry = self.get_tracform_field(db,resolved_name)							   	   

        if (entry['field'] is not None):									   	   
          # derive checked-state from database...								   	   
	  checkbox_def['cfg']['checked'] = (entry['value'] == checkbox_def['cfg']['value'])			   	   
        else:													   	   
          checkbox_def['cfg']['checked'] = self.to_boolean(checkbox_def['cfg']['checked'])			   	   

	if (checkbox_def['cfg']['debug']):									   	   
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s<" % (	   	   
	            command,											   	   
		    options,											   	   
		    name,resolved_name, 									   	   
		    str(checkbox_def['cfg']),									   	   
		    str(checkbox_def['xtras']), 								   	   
		    str(checkbox_def['xtra']),									   	   
		    str(entry)) 		     		     						   	   

        # map flag to html needs...										   	   
	if (checkbox_def['cfg']['checked']==True):								   	   
	  checkbox_def['cfg']['checked'] = 'checked="checked"'        						   	   
	else:   												   	   
	  checkbox_def['cfg']['checked'] = ''		        				   		   	   
		        						   					   	   
        # when submitting the form, checked checkboxes are transmitted, only.					   	   
	# => the update-processor will not know about unchecked ones.						   	   
	# => send a hidden field for all checkboxes to allow to find those.					   	   
        result += """						        						   
		     <INPUT					        						   
		      type='checkbox'				        						   
		      name='%s' 				        						   
        	      id='%s'					        						   
        	      class='%s'				        						   
		      value='%s'				        						   
        	      %s					        						   
		     >  					        						   
	 	     <INPUT					        						   
	 	      type="hidden"				        						   
	 	      name='%s' 				        						   
	 	      value='%s'				        						   
	 	     >  					        						   
		  """ % (checkbox_def['cfg']['name'   ],	        							
		  	 checkbox_def['cfg']['id'     ],	        							
		  	 checkbox_def['cfg']['class'  ],	        						   
		  	 checkbox_def['cfg']['value'  ],	        						   
		  	 checkbox_def['cfg']['checked'],	        							
		  	 placeholder_id,			        						   
		  	 checkbox_def['cfg']['name'   ] 	        							
		  	 )					        						   
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def create_radio(self, db, name, resolved_name, parameters, placeholder_id):
        # create radio...
	result    = ''											   	   
        radio_def = {'cfg'   : {'name'    : resolved_name,								 	 
	             		'checked' : False	     ,								 	 
	             		'value'   : 'true'	     ,								 	 
	             		'class'   : 'radio_css_class',								 	 
	             		'id'	  : 'radio_css_id'   ,								 	 
				'debug'   : False   									 	 
			       },											 	 
	      	     'xtras' : [],   											 	 
	      	     'xtra'  : {}    											 	 
	      	    }		     											 	 
															 	 
        # ...overwrite hardcoded defaults with user-defined values...							 	 
	radio_def = self.parse_options(parameters,radio_def)								 	 
															 	 
	# fetch state from database...											 	 
        msg,entry = self.get_tracform_field(db,resolved_name)								 	 

        if (entry['field'] is not None):										 	 
          # derive checked-state from database...									 	 
	  radio_def['cfg']['checked'] = (entry['value'] == radio_def['cfg']['value'])					 	 
        else:														 	 
          radio_def['cfg']['checked'] = self.to_boolean(radio_def['cfg']['checked'])					 	 

	if (radio_def['cfg']['debug']): 										 	 
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s<" % (		 	 
	            command,												 	 
		    options,												 	 
		    name,resolved_name, 										 	 
		    str(radio_def['cfg']),										 	 
		    str(radio_def['xtras']),										 	 
		    str(radio_def['xtra']),										 	 
		    str(entry)) 		     		     							 	 

        # map flag to html needs...											 	 
	if (radio_def['cfg']['checked']==True): 									 	 
	  radio_def['cfg']['checked'] = 'checked="checked"'        						   	 	 
	else:   													 	 
	  radio_def['cfg']['checked'] = ''		        				   			 	 

        result += """														   
		     <INPUT			     	        								 
		      type='radio'		     	        								 
		      name='%s' 		     	        								 
        	      id='%s'			     	        								 
        	      class='%s'		     	        								 
		      value='%s'		     	        								 
        	      %s			     	        								 
		     >  			     	        								 
		  """ % (radio_def['cfg']['name'   ],	        								   
		  	 radio_def['cfg']['id'     ],	        								   
		  	 radio_def['cfg']['class'  ], 	        								   
		  	 radio_def['cfg']['value'  ], 	        								   
		  	 radio_def['cfg']['checked']	        								   
		  	)			     	        								 
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def create_input(self, db, name, resolved_name, parameters, placeholder_id):
        # create input...
	result    = ''											   	   
        input_def = {'cfg'   : {'name'    : resolved_name,								   	   
	             		'value'   : ''  	     ,								   	   
	             		'size'    : 22  	     ,								   	   
	             		'class'   : 'input_css_class',								   	   
	             		'id'	  : 'input_css_id'   ,								   	   
				'debug'   : False   									   	   
			       },											   	   
	      	     'xtras' : [],   											   	   
	      	     'xtra'  : {}    											   	   
	      	    }													   	   

        # ...overwrite hardcoded defaults with user-defined values...							   	   
	input_def = self.parse_options(parameters,input_def)								   	   
															   	   
	# fetch state from database...											   	   
        msg,entry = self.get_tracform_field(db,resolved_name)								   	   

	if (input_def['cfg']['debug']): 										   	   
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s<" % (		   	   
	            command,												   	   
		    options,												   	   
		    name,resolved_name, 										   	   
		    str(input_def['cfg']),										   	   
		    str(input_def['xtras']),										   	   
		    str(input_def['xtra']),										   	   
		    str(entry)) 		     		     							   	   

        if (entry['field'] is not None):										   	   
          # ...overwrite hardcoded/user-defined default with database value...						   	   
	  input_def['cfg']['value'] = entry['value']									   	   

        result += """					     	    								   
		     <INPUT				     		  							   
		      name='%s' 			     		  							   
        	      id='%s'				     		  							   
        	      class='%s'			     		  							   
        	      value='%s'			     		  							   
        	      size=%s				     		  							   
		     >  				     		  							   
		  """ % (	       input_def['cfg']['name' ],	  							   
		  		       input_def['cfg']['id'   ],	  							   
		  		       input_def['cfg']['class'],	  							   
		  	 self.to_quote(input_def['cfg']['value']),  	  							   
		  		       input_def['cfg']['size' ]	  							   
		  	)				     		  							   
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def create_textarea(self, db, name, resolved_name, parameters, placeholder_id):
        # create text...
	result   = ''											   	   
        text_def = {'cfg'   : {'name'    : resolved_name,								   	   
	            	       'cols'	 : 10		   ,  								   	   
	            	       'rows'	 : 2		   ,  								   	   
	            	       'value'   : ''		   ,  								   	   
	            	       'class'   : 'text_css_class', 								   	   
	            	       'id'	 : 'text_css_id'   ,  								   	   
			       'debug'   : False   									   	   
			      },											   	   
	      	    'xtras' : [],    											   	   
	      	    'xtra'  : {}     											   	   
	      	   }		   											   	   

        # ...overwrite hardcoded defaults with user-defined values...							   	   
	text_def = self.parse_options(parameters,text_def)								   	   
															   	   
	# fetch state from database...											   	   
        msg,entry = self.get_tracform_field(db,resolved_name)								   	   

	if (text_def['cfg']['debug']):											   	   
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s<" % (		   	   
	            command,												   	   
		    options,												   	   
		    name,resolved_name, 										   	   
		    str(text_def['cfg']),										   	   
		    str(text_def['xtras']),										   	   
		    str(text_def['xtra']),										   	   
		    str(entry)) 		     		     							   	   

        if (entry['field'] is not None):										   	   
          # ...overwrite hardcoded/user-defined default with database value...						   	   
	  text_def['cfg']['value'] = entry['value']									   	   

        result += """				    										   
		     <TEXTAREA  	     		  									   
		      name='%s' 	     		  									   
        	      id='%s'		     		  									   
        	      class='%s'	     		  									   
        	      cols='%s' 	     		  									   
        	      rows='%s' 	     		  									   
		     >%s</TEXTAREA>		    	  									   
		  """ % (text_def['cfg']['name' ],  	  									   
		  	 text_def['cfg']['id'	],  	  									   
		  	 text_def['cfg']['class'],	  									   
		  	 text_def['cfg']['cols' ],	  									   
		  	 text_def['cfg']['rows' ],	  									   
		  	 text_def['cfg']['value']   	  									   
		  	)		     		  									   
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def create_select(self, db, name, resolved_name, parameters, placeholder_id):
        # create select...
	result = ''											   	   
        select_def = {'cfg'   : {'name'    : resolved_name     ,							   	   
	              		 'default' : None	       ,							   	   
	              		 'class'   : 'select_css_class', 							   	   
	              		 'id'	   : 'select_css_id'   , 							   	   
			         'debug'   : False   									   	   
			        },											   	   
	      	      'xtras' : [],  											   	   
	      	      'xtra'  : {}   											   	   
	      	     }													   	   

        # ...overwrite hardcoded defaults with user-defined values...							   	   
	select_def = self.parse_options(parameters,select_def)								   	   
															   	   
	# fetch state from database...											   	   
        msg,entry = self.get_tracform_field(db,resolved_name)								   	   

	if (select_def['cfg']['debug']):										   	   
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s< db=>%s<" % (		   	   
	            command,												   	   
		    options,												   	   
		    name,resolved_name, 										   	   
		    str(select_def['cfg']),										   	   
		    str(select_def['xtras']),										   	   
		    str(select_def['xtra']),										   	   
		    str(entry)) 		     		     							   	   

        option_section = ''												   	   
	for option in select_def['xtras']:										   	   
          if (select_def['xtra'][option]==''):										   	   
	    value = option												   	   
	    label = option												   	   
	  else: 													   	   
	    value = option												   	   
	    label = select_def['xtra'][option]										   	   

	  selected = False												   	   
	  														   	   
          if (select_def['cfg']['default'] is not None):								   	   
	    selected = (value == select_def['cfg']['default'])								   	   
	    														   	   
	  if (entry['field'] is not None):										   	   
	    selected = (value == entry['value'])									   	   

          # map flag to html needs...											   	   
	  if (selected==True):												   	   
	    selected = 'selected'          					  					   	   
	  else:  													   	   
	    selected = ''			        			  					   	   
															       
	  option_section += """			     	   						   		   	   
			       <OPTION  	        					   			   	   
		        	value='%s' %s										   	   
		               >%s</OPTION>     								  	   	   
		            """ % (self.to_quote(value),								   	   
		        	   selected,										   	   
		        	   label										   	   
		        	  )											   	   
															   	   
        result += """				        									   
		     <SELECT			     	    									   
		      name='%s' 		     	    									   
        	      id='%s'			     	    									   
        	      class='%s'		     	    									   
		     >%s</SELECT>		     	    									   
		  """ % (select_def['cfg']['name' ],  	    									   
		  	 select_def['cfg']['id'   ],  	    									   
		  	 select_def['cfg']['class'], 	    									   
		  	 option_section 	     	    									   
		  	)			     	    									   
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def create_submit(self, name, resolved_name, parameters, placeholder_id):
        # create submit...
	result = ''											   	   
        button_def = {'cfg'   : {'label'   : 'Send'	    ,							   	   
	              		 'class'   : 'buttons'      ,							   	   
	              		 'id'	   : 'button_css_id',   						   	   
			         'debug'   : False   								   	   
				},										   	   
	      	      'xtras' : [],  										   	   
	      	      'xtra'  : {}   										   	   
	      	     }												   	   

	button_def = self.parse_options(parameters,button_def)							   	   
														   	   
	if (button_def['cfg']['debug']):									   	   
	  result += "debug: command=>%s< options=>%s< name=>%s<>%s< cfg=>%s< xtras=>%s< xtra=>%s<" % (		   	   
	            command,											   	   
		    options,											   	   
		    name,resolved_name, 									   	   
		    str(button_def['cfg']),									   	   
		    str(button_def['xtras']),									   	   
		    str(button_def['xtra'])) 		     		     					   	   

        result += """					                        						
		     <INPUT			     			        					 
		      type='submit'		     			        					 
		      name='__SUBMIT'		     			        					 
        	      id='%s'			     			        					 
        	      class='%s'		     			        					 
		      value='%s'		     			        					 
		     >  			     			        					 
		  """ % (button_def['cfg']['id'     ],    		        						
		  	 button_def['cfg']['class'  ],  		        						
		  	 button_def['cfg']['label'  ] 			        						
		  	)			     			        					 
        return result			    	        					   		   	   

    # --------------------------------------------------------------------------------------------------------------------------

    def build_form(self, formatter,page,form_body):
        form_name      = 'form_name'
        form_css_id    = 'form_css_id'
        form_css_class = 'form_css_class'
        dest	       = str(formatter.req.href('/wikiforms/update'))
        backpath       = str(formatter.req.href(formatter.req.path_info))
        form_token     = str(formatter.req.form_token)

        yield """
	     	 <FORM 
		  class="printableform" 
             	  method="POST" 
	     	  action=%s
             	  name="%s"
             	  id="%s"
             	  class="%s"
             	 >
		 
		 %s
		 
	         <INPUT 
		  type="hidden" 
		  name="__BACKPATH" 
		  value=%s
		 >
	    	
	         <INPUT 
		  type="hidden"
        	  name="__FORM_TOKEN" 
		  value=%s
		 >
	    	
	         <INPUT 
		  type="hidden"
        	  name="__PAGE" 
		  value='%s'
		 >
	    	
	         </FORM>
	      """ % (dest,		     
	     	     form_name,
	     	     form_css_id,      
	     	     form_css_class,   
		     form_body,
		     backpath,
		     form_token,
		     page)
		     
    # --------------------------------------------------------------------------------------------------------------------------

    def to_quote(self,value):
        if value is None:
	  result = ''
	else:
	  result = value
          result = re.sub("'","&#39;",result)								      

	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def to_unquote(self,value):
        if value is None:
	  result = ''
	else:
	  result = value
          result = re.sub("&#39;","'",result)								      

	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def to_timestring(self,time_int, format='%Y-%b-%d %H:%M:%S'):
        if time_int is None:
	  result = 'unset-time'
	else:
          result = time.strftime(format, time.localtime(time_int))

	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def to_userstring(self,user):
        if user is None:
	  result = 'unset-user'
	else:
          result = user

	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def get_tracform_field(self,db,resolved_name):
    	cursor  = db.cursor()
	result  = {'field'     : None,
	           'value'     : '',
		   'updated_by': self.to_userstring(None),
		   'updated_on': None}

        get_sql = """
                     SELECT  field,value,updated_by,updated_on
                     FROM    wikiforms_fields
	             WHERE   field='%s'
                  """ % (self.to_quote(resolved_name))
	      
        cursor.execute(get_sql)
	
        row = []

	for field,value,updated_by,updated_on in cursor:
	  row.append({'field'      : self.to_unquote(field),
	              'value'      : self.to_unquote(value),
		      'updated_by' : self.to_userstring(updated_by),
		      'updated_on' : updated_on})

        if (len(row) == 1):
	  result = row[0]

        return get_sql,result

    # --------------------------------------------------------------------------------------------------------------------------

    def get_tracform(self,db):
    	cursor  = db.cursor()
	result  = []

        get_sql = """
                     SELECT  field,value,updated_by,updated_on
                     FROM    wikiforms_fields
                  """
	      
        cursor.execute(get_sql)
	
	for field,value,updated_by,updated_on in cursor:
	  result.append({'field'      : self.to_unquote(field),
	                 'value'      : self.to_unquote(value),
			 'updated_by' : updated_by,
			 'updated_on' : self.to_timestring(updated_on)})

        return get_sql,result

    # --------------------------------------------------------------------------------------------------------------------------

    def set_tracform_field(self,db,resolved_name,value,authname):
        cursor         = db.cursor()
        updated_on     = int(time.time())
        updated_by     = authname

    	set_sql = """
    		     UPDATE  wikiforms_fields
    		     SET     value='%s', updated_on='%s', updated_by='%s'
    		     WHERE   field='%s'
    		  """ % (self.to_quote(value),
		         updated_on,
			 updated_by,
			 self.to_quote(resolved_name))
    
	msg = "SQL %s=%s %s" % (resolved_name, value,set_sql)      
	self.log.debug(msg)

        cursor.execute(set_sql)
    
        if not cursor.rowcount:
    	  set_sql = """ 						       
    		       INSERT INTO  wikiforms_fields (field,value,updated_on,updated_by)  
        	       VALUES		             ('%s' ,'%s' ,'%s'      ,'%s'      )	      
    		    """ % (self.to_quote(resolved_name),
		           self.to_quote(value),
			   updated_on,
			   updated_by
			  )	       
    
  	  msg = "SQL %s=%s %s" % (resolved_name, value,set_sql)      
	  self.log.debug(msg)

    	  cursor.execute(set_sql)
    	  
        db.commit()
       
        return set_sql

    # --------------------------------------------------------------------------------------------------------------------------

    def delete_tracform_field(self,db,resolved_name):
    	cursor = db.cursor()				

        del_sql = """
        	     DELETE FROM wikiforms_fields
            	     WHERE  field='%s'
	    	  """ % (self.to_quote(resolved_name))

    	cursor.execute(del_sql)

    	db.commit()
	
	return del_sql

    # --------------------------------------------------------------------------------------------------------------------------

    def get_placeholder_id(self):
        WikiFormsMacro.placeholder_cnt += 1
        return "/%s:%s/" % (WikiFormsMacro.placeholder_cnt,random.randint(0,1000000000))

    # --------------------------------------------------------------------------------------------------------------------------

    def wiki_to_html(self, formatter, text):
        out = StringIO.StringIO()
        Formatter(formatter.env, formatter.context).format(text, out)
        return out.getvalue()

    # --------------------------------------------------------------------------------------------------------------------------

    def resolve_name(self,page,context,name):
        result = page  				 

        if (name!=''):   						 
          if (context!=''):
	    if (context[0]=='/'):
	      # absolute context...
	      result = context
	    else:
	      # relative context...
	      result += '/' + context
	
	  if (name[0]=='/'):	  
	    # absolute name...	  
	    result = name	  
	  else: 		  
	    # relative name...	  
	    result += '/' + name  
	  
	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def to_boolean(self,value):
        if (value is not None):
	  if isinstance(value, (bool)):
            result = value
	  elif (value.lower() in ['1','true','on','yes']):
            result = True
	  else:
	    result = False
	else:
	  result = False

	return result

    # --------------------------------------------------------------------------------------------------------------------------

    def get_piece(self,line):
        piece     = ''
	remainder = ''
	
	state = 'idle'
    
	for c in line:
	  if (state=='idle'):
	    if (c in [' ','\n','\t','\f']):
	      continue
	    else:
	      state = 'piece'
	      piece = ''
	      
	  if (state=='piece'):
	    if (c=='"'):
	      state = 'doublequoted'
	    elif (c == "'"):
	      state = 'singlequoted'
	    elif (c == ':'):
	      # terminator found...
	      state = 'remainder'
	    elif (c not in [' ','\n','\t','\f']):
	      piece += c
	  elif (state == 'doublequoted'):
	    if (c == '"'):
	      state = 'piece'
	    else:
	      piece += c
	  elif (state == 'singlequoted'):
	    if (c == "'"):
	      state = 'piece'
	    else:
	      piece += c
	  elif (state=='remainder'):
	    remainder += c

	return piece,remainder

    # --------------------------------------------------------------------------------------------------------------------------

    def parse_options(self,options,default):
        result   = default
	options += ' ' # ensure that last option is terminated...

	state      = 'idle'
	force_xtra = False

	for c in options:
	  if (state=='idle'):
	    if (c in [' ',':','\n','\f']):
	      # skip...
	      if (c==':'):
	        force_xtra = True
	      continue
	    else:
	      state = 'name'
	      name  = ''
	      
	  if (state=='name'):
	    if (c=='"'):
	      state = 'doublequotedname'
	    elif (c == "'"):
	      state = 'singlequotedname'
	    elif (c=='='):
	      state = 'value'
	      value = ''
	    elif (c in [' ',':','\n','\f']):
	      # terminator found...
	      if ((name not in result['cfg']) or (force_xtra==True)):
	        result['xtras'].append(name)
	        result['xtra' ][name]=''
	      else:
	        result['cfg'  ][name]=''
		
	      if (c==':'):
	        force_xtra = True

	      state = 'idle'
	    else:
	      name += c
	  elif (state == 'doublequotedname'):
	    if (c == '"'):
	      state = 'name'
	    else:
	      name += c
	  elif (state == 'singlequotedname'):
	    if (c == "'"):
	      state = 'name'
	    else:
	      name += c
	  elif (state=='value'):
	    if (c=='"'):
	      state = 'doublequotedvalue'
	    elif (c == "'"):
	      state = 'singlequotedvalue'
	    elif (c in [' ',':','\n','\f']):
	      # terminator found...
	      if ((name not in result['cfg']) or (force_xtra==True)):
	        result['xtras'].append(name)
	        result['xtra' ][name]=value
	      else:
	        result['cfg'  ][name]=value

	      if (c==':'):
	        force_xtra = True

	      state = 'idle'
	    else:
	      value += c
	  elif (state == 'doublequotedvalue'):
	    if (c == '"'):
	      state = 'value'
	    else:
	      value += c
	  elif (state == 'singlequotedvalue'):
	    if (c == "'"):
	      state = 'value'
	    else:
	      value += c

	return result

    # --------------------------------------------------------------------------------------------------------------------------
