# Integration of Drupal with Trac.

from trac.core import *
from trac.db.api import DatabaseManager
from trac.config import Option
from acct_mgr.api import IPasswordStore
from hashlib import md5

# Some random notes:
# - We don't have groups and the like.
# - The "users" table contains (uid, name, pass) - we need only the last 2
# - The password seems to be MD5'd. Notes on drupal.org pointed to this.
class DrupalIntegration(Component):
	implements(IPasswordStore)

	# Database option.
	database = Option('account-manager', 'drupal_database', None,
		 'Drupal database URI.')

	# Table prefix.
	tblpre = Option('account-manager', 'drupal_tblpre', None,
		 'Drupal table prefix.')

	def get_users(self):
		""" Pull list of users from Drupal. """
		db = self.env.get_db_cnx()
		cur = db.cursor()
		cur.execute("SELECT name FROM %susers")
		for name in cursor:
			yield name

	def has_user(self, user):
		""" Check for a user. """
		db = self.env.get_db_cnx()
		cur = db.cursor()
		cur.execute("SELECT * FROM users WHERE name=%s", user)
		for name in cur:
			return True
		return False

	def set_password(self, user, password):
		""" Set the user's Trac and Drupal password. """
		hashed = md5(password).hexdigest()
		db = self.env.get_db_cnx()
		cur = db.cursor()
		cur.execute("UPDATE users SET pass=%s WHERE name=%s", hashed, user)
		db.commit()

	def check_password(self, user, password):
		""" Very alike the above. """
		hashed = md5(password).hexdigest()
		db = self.env.get_db_cnx()
		cur = db.cursor()
		cur.execute("SELECT pass FROM users WHERE name=%s, pass=%s", user, hashed)
		# Hackish code to only check one account
		for pass in cur:
			return pass == hashed

	def delete_user(self, user):
		""" Delete Drupal and Trac account. """
		if not self.has_user(user):
			return False
		db = self.env.get_db_cnx()
		cur = db.cursor()
		cur.execute("DELETE FROM users WHERE name=%s", user)
		db.commit()
		return True
