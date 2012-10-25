import os
from trac.env import Environment
# Dump info required by SVN pre-commit hooks

def dumpSVNTracInfo(env, grp):
	db = env.get_read_db()
	cursor = db.cursor()
	cursor.execute ("""select id,status,owner from ticket where status <> 'closed'""")
	for id,status,owner in cursor:
		print 'T'+'|'+env.project_name+'|#' + str(id) +'|'+ owner+ '|'+status+'|'
	cursor = db.cursor()
	cursor.execute ("""select username,action from permission where action = %s""", (grp,))
	for username,action in cursor:
		print 'G'+'|'+env.project_name+'|' + action +'|'+ username +'|'
		

if __name__ == '__main__':
	path=os.environ['TRAC_PROJ_DIR']
	grp = os.environ['SVN_PRIV_TRAC_GRP']
	listall = os.listdir(path)
	for infile in listall: 
		env = Environment(os.path.join(path,infile))
		dumpSVNTracInfo(env, grp)