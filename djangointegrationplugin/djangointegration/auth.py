# -*- coding: utf-8 -*-

# Copyright 2010 Guilhelm Savin

from trac.config import Option
from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web.main import IAuthenticator
from trac.env import IEnvironmentSetupParticipant

from trac.util.html import html

from djangointegration.trac.web.session import Session

class DjangoIntegrationPlugin(Component):
    implements(IAuthenticator, INavigationContributor, IEnvironmentSetupParticipant)

    logout_url = Option( 'djangointegration', 'logout_url', '#',
      """Url used to log out.""" )
    login_url = Option( 'djangointegration', 'login_url', '#',
      """Url used to log in.""" )
    registration_url = Option( 'djangointegration', 'registration_url', '#',
      """Url used to register in.""" )

# IAuthenticator

    def authenticate(self, req):
	self.log.debug('authenticate wia DjangoIntegration')
	
	session = Session(self.env,req)
	
	if session.django_user_data:
	  return session.django_user_data.username
	else:
	  return "anonymous"

# INavigationContributor

    def get_active_navigation_item(self, req):
	  return 'login'

    def get_navigation_items(self, req):
	  if req.authname and req.authname != 'anonymous':
	      yield 'metanav', 'login', req.authname
	      yield 'metanav', 'logout', html.a('sign out', href=self.logout_url)
	  else:
	      yield 'metanav', 'login', html.a('sign in', href=self.login_url)
	      yield 'metanav', 'logout', html.a('register', href=self.registration_url)

# IEnvironmentSetupParticipant

    def environment_created(self):
      pass

    def environment_needs_upgrade(self, db):
    
      def inline_django_get_known_users(environment = None, cnx=None):
	
	from django.contrib.auth.models import User as DjangoUser
	
	if DjangoUser.objects.count() > 0:
	  
	  for user in DjangoUser.objects.all():
	    yield (user.username,user.get_full_name(),user.email)

      self.env.get_known_users = inline_django_get_known_users
      self.env.log.info('users list is now the django user list')
      
      return False   
	
    def upgrade_environment(self, db):
      pass
