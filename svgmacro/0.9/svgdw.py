# Set this to the directory you want the images stored in. Web server must have write access.
images_folder = 'D:/web/phpBB/branches/phpBB-2.0.22/files/svgdw'
# Base URL of the folder.
images_url = 'http://ezsrv/files/svgdw'

# Adapted from the Image.py macro created by Shun-ichi Goto <gotoh@taiyo.co.jp> 
# 
# Display image in attachment or repository into the wiki page.
# 
# First argument is filename (file spec).
# 
# The file specification may refer attachments:
#  * 'module:id:file', with module being either 'wiki' or 'ticket',
#    to refer to the attachment named 'file' in the module:id object
#  * 'id:file' same as above, module defaulted to 'wiki' (id can be dir/dir/node)
#  * 'file' to refer to a local attachment named 'file'
#    (but then, this works only from within a wiki page or a ticket).
# 
# Ex.
#   [[Image(photo.jpg)]]                           # simplest
# 
# You can use image from other page, other ticket or other module.
#   [[Image(OtherPage:foo.bmp)]]    # if current module is wiki
#   [[Image(base/sub:bar.bmp)]]     # from hierarchical wiki page
#   [[Image(#3:baz.bmp)]]           # if in a ticket, point to #3
#   [[Image(ticket:36:boo.jpg)]]
#   [[Image(source:/images/bee.jpg)]] # straight from the repository!


import os
import re
import string
import shutil 
import md5
from trac.attachment import Attachment

def execute(hdf, txt, env):
	# args will be null if the macro is called without parenthesis.
	if not txt:
		return ''
	# parse arguments
	# we expect the 1st argument to be a filename (filespec)
	args = txt.split(',')
	if len(args) == 0:
	   raise Exception("No argument.")
	filespec = args[0]
	# parse filespec argument to get module and id if contained.
	parts = filespec.split(':')
	if len(parts) == 3:                 # module:id:attachment
		if parts[0] in ['wiki', 'ticket']:
			module, id, file = parts
		else:
			raise Exception("%s module can't have attachments" % parts[0])
	elif len(parts) == 2:               # #ticket:attachment or WikiPage:attachment
		# FIXME: do something generic about shorthand forms...
		id, file = parts
		if id and id[0] == '#':
			module = 'ticket'
			id = id[1:]
		else:
			module = 'wiki'
	elif len(parts) == 1:               # attachment
		file = filespec
		# get current module and id from hdf
		module = hdf.getValue('args.mode', 'wiki')
		if module == 'wiki':
			id = hdf.getValue('args.page', 'WikiStart')
		elif module == 'ticket':
			id = hdf['args.id'] # for ticket
		else:
			# limit of use
			raise Exception('Cannot use this macro in %s module' % module)
	else:
		raise Exception( 'No filespec given' )
	try:
		attachment = Attachment(env, module, id, file)
		org_path = attachment.path
		return svg_render(images_folder, images_url, org_path)
	except:
		return '%s not found' % (filespec)

def svg_render(images_folder, images_url, org_path):
	md5sum = md5.new(org_path).hexdigest()
	img_path = '%s/%s.svg' % (images_folder, md5sum)
	url = '%s/%s.svg' % (images_url, md5sum)
	img_time=org_time=''
	try:
		if not os.access(img_path, os.F_OK):
			shutil.copy2(org_path, img_path)
		else:
			org_time = os.path.getmtime(org_path)
			img_time = os.path.getmtime(img_path)
			if org_time != img_time:
				shutil.copy2(org_path, img_path)
	except:
		raise Exception(  'can not render svg file')
	try:
		f = open(img_path, 'r')
		svg = f.readlines()
		f.close()
		svg = "".join(svg).replace('\n', '')
		w = re.search('width="([0-9]+)(.*?)" ', svg)
		h = re.search('height="([0-9]+)(.*?)"', svg)
		(w_val, w_unit) = w.group(1,2)
		(h_val, h_unit) = h.group(1,2)
		# Graphviz seems to underestimate height/width for SVG images,
		# so we have to adjust them. The correction factor seems to be constant.
		[w_val, h_val] = [ 1.2 * x for x in (int(w_val), int(h_val))]
		dimensions = 'width="%(w_val)s%(w_unit)s" height="%(h_val)s%(h_unit)s"' % locals()
	except:
		dimensions = 'width="100%" height="100%"'
	return '<object type="image/svg+xml" data="%s" %s>\
	</object>\n' % (url,dimensions)
