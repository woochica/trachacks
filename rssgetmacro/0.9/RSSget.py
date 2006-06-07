"""Example macro."""
import urllib
import time
import string
import os
import httplib
import urllib2
import StringIO
from xml.dom import minidom
from trac.util import escape

## Usage: [[RSSget(http://www.example.com/feed.xml)]]
##


CACHE_DIR = "/tmp";
CACHE_ID = "tracrss"
CACHE_INTERVAL = 7500
News = "" # output
RESULTS_FULL = 1;
RESULTS_TOTAL = 5;


# Flow
# 1. check cache
# 2. if there is a hit, make sure its fresh
# 3. if cached obj fails freshness check, fetch remote
# 4. if remote fails, return stale object, or error

## PART ONE: check the cache
def cache_lookup(url):
	# generate a positive hash of the url
	cache_id = abs(hash(url))
	# print cache_id
	# look through the cache dir for matches
	cached_files = os.listdir(CACHE_DIR + "/" + CACHE_ID)
	for filename in cached_files:
		# print cached_files
		cached_file = string.split(filename, sep=CACHE_ID)[0]
		#check the hash
		if (cache_id == int(cached_file)):
			return filename


## PART TWO: check for freshness
def freshness_check(filename, interval):
	olddate = string.split(filename, sep=CACHE_ID)[1]
	time_elapsed = time.time() - float(olddate)
	if (time_elapsed > interval):
		return False
	else:
		return True

## PART THREE: if the cached one fails the freshness test
## make a new filename for the new get.

def create_filename(url):
	# creates a uniqe but parseable filename for the cachefile
	# consising of:
	# 	hash of url
	#	cache id
	#	timestamp of creation
	# you can get the url hash and timestamp back with:
	#	struct = string.split(filename, sep=CACHE_ID)
	urlhash = str(abs(hash(url)));
	now = time.time()
	filename = urlhash + CACHE_ID + str(now);
	return filename
	
## burn the old one
def remove_old_cache(url):
	filename = cache_lookup(url)
#	print filename
	os.remove(CACHE_DIR + "/" + CACHE_ID + "/" + filename)

## hell, burn all of 'em
def clear_cache(url):
	# generate a positive hash of the url
	cache_id = abs(hash(url))
	# print cache_id
	# look through the cache dir for matches
	cached_files = os.listdir(CACHE_DIR + "/" + CACHE_ID)
	for filename in cached_files:
		# print cached_files
		cached_file = string.split(filename, sep=CACHE_ID)[0]
		#check the hash
		if (cache_id == int(cached_file)):
			os.remove(CACHE_DIR + "/" + CACHE_ID + "/" + filename)

# a useful tool	
def _mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        #print "_mkdir %s" % repr(newdir)
        if tail:
            os.mkdir(newdir)

#just make sure it's there, every time..

_mkdir(CACHE_DIR + "/" + CACHE_ID)

	
## write stuff to a new cache

def write_to_cache(url, contents):
	clear_cache(url)
	#generate the filename
	filename = create_filename(url)
	#make sure the directory's there
	_mkdir(CACHE_DIR + CACHE_ID)
	#open the right file
	cachefile = open(CACHE_DIR + "/" + CACHE_ID + "/" + filename, 'w')
	#cram in the contents
	cachefile.write(contents)
	#shoehorn it back closed
	cachefile.close


# the actual xml parser

def remote_url_get(url):
	request = urllib2.Request(url) 
	request.add_header('User-Agent', 'TracRSS')
	opener = urllib2.build_opener()                                   
	feeddata = opener.open(request).read()
	write_to_cache(url, feeddata)
	return feeddata

def local_file_read(filename):
	cachefile = open(CACHE_DIR + "/" + CACHE_ID + "/" + filename, 'r')
	contents = cachefile.read()
	return contents

#parse into xml
def parse_file(feeddata):
	
	rss_snippets = ""
	titles = []
	links = []
	words = []
		
	xmlstring = StringIO.StringIO(feeddata)
	# print str(xmlstring)
	xmldoc = minidom.parse(xmlstring)
	Itemlist = xmldoc.getElementsByTagName('item')
	
	for Item in Itemlist:
		for node2 in Item.getElementsByTagName("title"):
			title = node2.firstChild.data
			titles.append(title)
		for node2 in Item.getElementsByTagName("link"):
			link = node2.firstChild.data
			links.append(link)
		for node2 in Item.getElementsByTagName("description"):
			description = node2.firstChild.data
			words.append(description)
	 
	rss_snippets += "<dl>\n"
	for i in range(RESULTS_FULL):
		rss_snippets += "<dt><a href='" + links[i] + "'>" + titles[i] + "</a></dt>\n"
		rss_snippets += "<dd><p>" + words[i] + "</p></dd>\n"
	
	for i in range(RESULTS_FULL, RESULTS_TOTAL):
		rss_snippets += "<dt><a href='" + links[i] + "'>" + titles[i] + "</a></dt>\n"
	rss_snippets += "</dl>\n"
	
	return rss_snippets
	

# the master logic.

def rss_get_url(url):
	# 1. check cache
	cache_file = cache_lookup(url)
#	print cache_file
	if cache_file:
#		print "checking freshness"
		cache_freshtest = freshness_check(cache_file, CACHE_INTERVAL)
#		print cache_freshtest
	# 2. if there is a hit, make sure its fresh
		if cache_freshtest:
#			print "file is fresh"
			cache_contents = local_file_read(cache_file)
			parsed_rss = parse_file(cache_contents)
			#print parsed_rss
			return parsed_rss
	# 3. if cached obj fails freshness check, fetch remote
		else:
#			print "file is stale, getting remote"
			remote_rss = remote_url_get(url)
			parsed_rss = parse_file(remote_rss)
			return parsed_rss
	else:
#		print "there is no cache file, getting remote"
		remote_rss = remote_url_get(url)
		parsed_rss = parse_file(remote_rss)
		return parsed_rss
		
	# 4. if remote fails, return stale object, or error
	# not implemented
	
#print rss_get_url('http://sxip.org/blog/?feed=rss')

def execute(hdf, txt, env):
    News = rss_get_url(txt)
        
    # args will be null if the macro is called without parenthesis.
    args = txt or 'No arguments'

    return News




