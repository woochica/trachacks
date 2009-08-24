# Sarah Strong.  sarah.e.strong@gmail.com

from genshi import HTML

def make_recommendation_box(self, req):

	html = ""

	contact = get_suggested_contact(self,req)
	
	username = req.authname
	if username == "anonymous":
		html +=	"<h2>Please log in to view suggested contacts</h2>"

	elif contact is None:
		html += "<h2>You have no suggested contacts.</h2><br />Try committing changes to the repository to see suggestions."
	else:
	# Right now this is a pile of absurdity. We really need to find out if
	# trac and vc logins are typically linked to email addresses so we can identify people
		html += '''<h2>Have you spoken to...</h2>
			<div style="padding:10px">
				<h3>%s?</h3>
				<p><a href="mailto:coworker@example.com">%s@%s.com</a></p>
				<h4>Why?</h4>
				<p>%s is an expert on these files you've been working on:</p>
				<ul>
			''' % (contact.name, contact.name, contact.name, contact.name)
		for file in contact.get_top_common_files(4):
			html += '<li>' + file + '</li>'
		html += '''
				</ul>
			</div>
			'''

	html = HTML(html)
	return html



def get_suggested_contact(self, req):
	'''
	Chooses the recommended colleague to display in the social networking tab
	First pass logic: Recommend colleague with most expertise in the files you committed last.
	Only consider as same person exactly equal svn & trac login names
	TODO: perhaps, if person not found, prompt for svn name?Seems bad security, but nothing really private shared yet
	'''


	# We only give suggestions to logged in users
	username = req.authname
	if username == 'anonymous':
		suggested_contact = None

	db = self.env.get_db_cnx()
	cursor = db.cursor()	

	# For each file edited (repetitions intentional for
	# strengthening relations), add expertise of other authors to a dict
	# file = { author : strength, author2 : strength }

	cursor.execute("SELECT path, author, strength \
			FROM expertise \
			WHERE author != %s AND path IN ( \
							SELECT n.path \
							FROM node_change n, revision r \
							WHERE n.rev = r.rev AND r.author = %s \
							)", (username, username))

	
	colleagues = []
	for file, author, strength in cursor:
		entry = None
		for i in range( len(colleagues) ):
			if colleagues[i].name == author:
				entry = i
		if entry is None:
			entry = -1
			colleagues.append(Author(author, username))
		colleagues[entry].add_file(file, strength)	
		
	if len(colleagues) == 0:
		return None
	
	suggested_contact = max(colleagues)
	return suggested_contact

class Author():

	def __init__(self, name, username):
		self.compared_to = username 
		self.name = name
		self.total_strength = 0
		self.files = {}

	def __cmp__(self, other):
		return cmp(self.total_strength, other.total_strength)

	def add_file(self, file, strength):
		if file in self.files:
			self.files[file] += strength
		else:
			self.files[file] = strength
		self.total_strength += strength

	def get_top_common_files(self, num=1):
		# max_files = list of (file, strength) tuples sort in non-increasing order
		max_files = sorted(self.files.items(), key=lambda (k,v): (v,k), reverse=True)
		#return max_files[0:num]
		return self.files
