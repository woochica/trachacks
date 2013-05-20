import codecs
import os
import commands
import re
import urllib
import dircache
import logging
import string, time
# import random, md5

from trac.core import *
from trac.config import Option, Section , Configuration
from trac.search import ISearchSource
from trac.attachment import IAttachmentChangeListener

class AttachmentSearchPlugin(Component): 
	implements( ISearchSource, IAttachmentChangeListener )

        def _absolute_index_dir( self ):
                return os.path.join( self.env.path , 'attachments' , 'index' )

        absolute_index_dir = property(_absolute_index_dir)


	swish = Option('attachment', 'swish',
		"""Absolute path to swish binary.""")

	seat = Option('attachment', 'seat',
		"""Absolute path to trac-seat utility""")

        #############################
	# IAttachmentChangeListener #
        #############################
	
	def attachment_added( self , attachment ):

		if self._create_metafile (attachment):
			self._build_index()
			return True
		else:
			self.env.log.error('Error while creating meta:%s' % attachment.filename )
			return False

	def attachment_deleted( self , attachment ):

		meta_path = attachment.path + '.meta'

		# Remove meta file
		try:
			 os.remove( meta_path )
		except:
			self.env.log.warn ('Cannot delete %s.meta' % attachment.filename )

		# Rebuild index
		self._build_index()
		return

	###########################
	# ISearchSource listeners #
        ###########################

	def get_search_filters(self, req):
		if req.perm.has_permission('WIKI_VIEW'):
			yield('attachments', 'Attachments')

	def get_search_results(self, req, keywords, filters):
		if not 'attachments' in filters:
			return

		# Prepare keywords
		query = ''
		for word in keywords :
			query = query + word + ' '
		query.rstrip(' ')
		self.env.log.debug ('Search query: %s' % query )

		# Run external command to get raw search result
		index_file = self._get_index_file()
		if not index_file:
			return
		index_dir  = self.absolute_index_dir
 
		cmd = 'cd %s && %s -f %s -w %s' % ( index_dir , self.swish , index_file , query )
		self.env.log.debug ( 'command % s =' %  cmd)
		error , output = commands.getstatusoutput( cmd )
		if error :
			# TODO:Just return or raise exception here?
			self.env.log.error ( output )
			raise Exception( output )
			return

		# Parse output of the command
		for line in output.split('\n'): 
			line = line.strip(' ')
			if line and line[0] != '#' :
				#sel.env.log.debug ( 'line = %s ' % line )
				# This is not a comment... let's parse the line
				pattern  = re.compile ('^(\d*) (.*)/(.*)\.meta "(.*)" (\d*)$')
				hit      = pattern.match ( line )
				if hit:
					sw_rank      = hit.group(1)
					sw_abs_dir   = hit.group(2)
                                        sw_filename  = hit.group(3)
                                        sw_title     = hit.group(4)
                                        sw_end       = hit.group(5)

					regexp = '^' + self.env.path + '/attachments/(.*)$'
					p = re.compile(regexp)
					m = p.match ( sw_abs_dir )
					if m :
						sw_dir = m.group(1)
	                                        file = os.path.join( sw_abs_dir , sw_filename )

					else:
						sw_dir = sw_abs_dir
	                                        file = os.path.join( self.env.path , 'attachments' , sw_dir , sw_filename )
			
					# Build variables that we'll return for this hit
					relative_url  = 'attachment/%s/%s'  % ( sw_dir , sw_filename )
					title         = 'Attachment::%s/%s' % ( sw_dir , urllib.url2pathname(sw_filename) )
					if os.path.exists (file): 
	                                        date = os.path.getmtime( file )
					else:
						return
					excerpt	      = self._make_excerpt ( file + '.meta' , keywords )					

					# Return the hits
					yield ( relative_url , title , date , 'SearchAttachments' , excerpt )
 

      	####################
	# Private methods  #
       	####################

	def _make_excerpt ( self, metafile , keywords ):
		"""Create an exceprt, starting from the first line before first matching keyword"""

                handle = codecs.open( metafile , 'r' , 'utf_8' , 'ignore' )
                if handle:
                	content  = handle.read( 500000 )    # Read ~1Mbyte maximum

			# Transform wildchar that may exist in the query
			# to a regexp equivalent
			wildchar = keywords[0].replace('*','[a-z0-9]*')
                        regexp = '(\n).* ?(%s)' % wildchar
                        m = re.compile(regexp , re.IGNORECASE ).search ( content )
                        if m:
                        	startline =  m.start(1)
                               	start     =  m.start(2)
				if start - startline > 100 : 
					startline = start - 100
					begin = '... '
				else :	
					begin = ''
                                length  = 500                          # Number of char in the excerpt
                        	if startline:
                                	excerpt = begin + content[startline:start+length] + ' ...'
                                else:
                                       	excerpt = begin + content[0:length] + ' ...'
                	else:
                                excerpt = 'Excerpt not available... (cannot find first keyword)'
		else:
                	excerpt = 'Excerpt not available... (cannot read the meta file)'

		# Cleaning up some unprintable added by catdoc
		excerpt = multiple_replace( { '\x0a':' ' , '\x0c':' ' }  , excerpt )
 
		return excerpt

	def  _get_index_file ( self ) :
                """Returns the most recent index file found in the index directory"""

		if not os.path.isdir( self.absolute_index_dir ):
			self.env.log.warning ('index directory does not exist')
			return None

                # Read all the matching index.* files into a dictionary
                all = {}
                for item in dircache.listdir( self.absolute_index_dir ) :
                        path = os.path.join ( self.absolute_index_dir , item )

                        prefix_pattern = re.compile('^index\.swish-e\.(.*)$') 
			prefix = prefix_pattern.match ( item )
                        if prefix :
                                # Can be index.xxxx or index.xxxx.prop or index.xxxx.temp
                            	key = prefix.group(1)

                        	if re.compile('^.*\.temp$').match ( key ) :
                                	# Ignore files ending with *.temp
                                	break

                                if not re.compile('^.*\.prop$').match( key ):
                                        # This is an index file ...
                                        # ... add last modification time
                                        all[path] = os.path.getmtime(path)


		# Do we have indexes in the 'all' dictionary?
		if not all:
			self.env.log.warning ('attachments/index does not contain any index file')
			return None

                # Sort the indexes dictionary by increasing value
                sorted_dict = list(all.iteritems())
                sorted_dict.sort(lambda i1, i2: cmp(i1[1], i2[1]))

		# Get last tuple
         	last_index = sorted_dict.pop()
		return last_index[0]

	def _build_index( self , conf_file = 'swish.config' ):
		"""Build a new index by lauching the build_index script as a background process"""
	
		self.env.log.info ('Starting index update')
		cmd = '%s "%s" index -s "%s" -c' % (  self.seat , self.env.path , self.swish )
		self.env.log.debug ( cmd  )
		# Script is launched as a background process
		# ... so we'll return immediately
		os.system( cmd + ' &' )
		return


	def _create_metafile ( self , attachment ) :
		"""Create a metafile (ie. a text version) for the attachement."""
		"""Only extensions with a filter.* command defined in trac.ini will be processed."""

		meta_file = attachment.path + '.meta'
		extension = self._get_extension ( attachment )

		if not extension:
			msg = '.meta not created for %s (cannot determine file type)' % attachment.filename
			self.env.log.error( msg )
			return False

		self.env.log.debug ('Uploaded file with extension = %s' % extension)
		
		# Iterate over filter.* in the [attachment] section of the config file
		# to build a dictionary of extension:command
	        filters = { 'txt' : 'cp -rf "%s" "%s"' }
                for entry in self.config['attachment'] :
                        p = re.compile('filter.([a-zA-Z0-9]*)')
                        m = p.match ( entry )
                        if m:
                                format = m.group(1).lower()
                                filters[format] = self.config['attachment'].get(entry)

		# Is there a known filter for this extension?
		if extension in filters :

			# Converting to text with the command defined for this extension
			if os.path.exists( meta_file ):
				os.remove ( meta_file )		

			cmd = filters[extension] % ( attachment.path , meta_file )
			self.env.log.debug( "Converting to text: %s" % cmd )
			error , output = commands.getstatusoutput ( cmd )

			# Command sucessful?
			if error:
				self.env.log.error( 'Error when converting .%s to ext :: %s' % ( extension , output) )
				return False
			else:
				self.env.log.info('File %s succesfully converted ot text' % attachment.filename )
				return True
		# Unknown extension
		else:
			self.env.log.warn ('No filter defined for this extension. Add a filter.%s entry in trac.ini' % extension )
			return False

		return False

	def _get_extension ( self , attachment ):

		pattern  = re.compile( '^.*\.([a-zA-Z0-9]*)$' )
	        suffix = pattern.match( attachment.filename.strip() )

	        if suffix:
			ext = suffix.group(1).lower()
			# Synonyms for txt
			if ext in [ 'txt' , 'text' , 'xml' ]:
				return 'txt'
			else:
				return ext

		# No suffix...may be a text file
                elif is_text_file ( attachment.path ):
                        return 'txt'

		# Cannot determine type
	        else:
			return False


##########################
# Some utility functions #
##########################

def is_text( content ):
	"""Determines if the content is text"""

	text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
	_null_trans = string.maketrans("", "")

 	if "\0" in content:
       		return False
    
	if not content:  # Empty files are considered text
        	return True

	# Get the non-text "binary" characters
	binary = content.translate( _null_trans , text_characters )

	# If more than 30% non-text characters, then
	# this is considered a binary file
	if len(binary) <= len(content) * 0.3:
		return True

	return False

def is_text_file(  filepath , blocksize = 512 ):
	"""Read the first 512 bytes of the specified file"""
	"""Returns True if it's a text file. False otherwise"""

	if is_text(open(filepath).read(blocksize)):
		return True
	else:
		return False

def multiple_replace( dict , text): 
	""" Replace in 'text', all occurences of keys specified in the input
  	dictionary with its corresponding value.  Returns the new tring.""" 

  	# Create a regular expression  from the dictionary keys
  	regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  	# For each match, look-up corresponding value in dictionary
	return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

