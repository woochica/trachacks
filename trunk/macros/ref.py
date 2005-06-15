import re

anchor_re = re.compile('[^\w\d]+')

def execute(hdf, args, env):
	return "<a href='#%s' title='Go to %s'>%s</a>" % (anchor_re.sub("", args), args, args)
