"""
A quick and dirty captcha for use with AccountManagerPlugin registration
"""
# Plugin for trac 0.11

from acct_mgr.web_ui import RegistrationModule

from componentdependencies import IRequireComponents

from genshi.builder import Markup
from genshi.builder import tag
from genshi.filters.transform import Transformer

from skimpyGimpy import skimpyAPI

from trac.config import Option
from trac.core import *
from trac.web import IRequestFilter
from trac.web import ITemplateStreamFilter
from trac.web.chrome import add_warning 

from utils import random_word
from web_ui import ImageCaptcha
import time

class LoginCaptcha(Component):

    ### class data
    implements(IRequestFilter, ITemplateStreamFilter, IRequireComponents)
    
    
    dict_file = Option('captchaauthplus', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")
    captcha_type = Option('captchaauthplus', 'type',
                          default="png")

                          
    last_capcha = {};
    should_display_capcha={};
   
    ### IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        if req.path_info.strip('/') == "login":            
                       
            if req.method == "POST":
                
                #Fix in case the server was restarted after login screen has been displayed
                if  not (req.remote_addr in self.should_display_capcha):
                    add_warning(req, "An error occurred. Please try again.") 
                    req.redirect(req.href('login', failed=''))
                
                if self.should_display_capcha[req.remote_addr]==True:
                    correct_answer = req.session.get('captcha', False)                            
                    correct_answer = self.last_capcha[req.remote_addr]
                    req.session.save()                
                    if req.args['captcha'].lower() != correct_answer:      
                        req.redirect(req.href('login', failed=''))
                    
            if req.method == "GET":
                if 'failed' in req.args and req.authname == 'anonymous':   
                    if req.remote_addr in self.should_display_capcha:
                        add_warning(req, "You typed the wrong word. Please try again.")
                        
            
            if req.method == "GET" and req.authname != 'anonymous':
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                cursor.execute("""SELECT * FROM login_attempts WHERE ip= '%s' """ % req.remote_addr)
                row1 = cursor.fetchone()
                db.close()  
                if row1:   
                    #bann expired. This prevents users from loggin in with a known account to remove capcha
                    #and then attack another account.
                    if (row1[1] > 2) and (int(time.time()) >= (int(row1[2]) + 300) ):               
                        db = self.env.get_db_cnx()
                        cursor = db.cursor()
                        cursor.execute("""DELETE FROM login_attempts WHERE ip= '%s' """ % req.remote_addr)
                        db.commit()
                        db.close()
            
            if req.method == "POST" and req.authname == 'anonymous':
                #Register failed login attempt
                db = self.env.get_db_cnx()
                cursor = db.cursor()
                
                cursor.execute("""SELECT ip FROM login_attempts WHERE ip= '%s' """ % req.remote_addr)
                row = cursor.fetchone()
                
                if not row:
                    # first invalid attempt                    
                    cursor.execute("INSERT INTO login_attempts (ip,attempts,timestamp) "
                       "VALUES (%s, %s, %s)", (req.remote_addr, 1, int(time.time())))
                    db.commit()        
                else:
                    cursor.execute("""UPDATE login_attempts SET 
                        attempts=attempts+1, timestamp=%s 
                        WHERE ip='%s' """ % (int(time.time()),req.remote_addr))
                    db.commit()
                
                db.close()
                                        
        return handler

    # for ClearSilver templates
    def post_process_request(self, req, template, content_type):
        """Do any post-processing the request might need; typically adding
        values to req.hdf, or changing template or mime type.
        
        Always returns a tuple of (template, content_type), even if
        unchanged.

        Note that `template`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (for 0.10 compatibility; only used together with ClearSilver templates)
        """

        return (template, content_type)

    # for Genshi templates
    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """
        return (template, data, content_type)


    ### ITemplateStreamFilter method

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """
        # move these someplace sensible?
        form_id = "acctmgr_loginform" # id of the login form
        msg = "Please enter the text below to prove you're not a machine."
        
               
        if filename == "login.html":
        
             #Check whether to display capcha.
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("""SELECT * FROM login_attempts WHERE ip= '%s' """ % req.remote_addr)
            row1 = cursor.fetchone()
            db.close()
            self.should_display_capcha[req.remote_addr] = False
            if row1:
                if row1[1] > 2:
                    self.should_display_capcha[req.remote_addr] = True                

            if self.should_display_capcha[req.remote_addr]==True:
                word = random_word(self.dict_file)
                req.session['captcha'] = word
                req.session.save()
                self.last_capcha[req.remote_addr] = word
                if self.captcha_type == 'png':
                    captcha = '<img src="%s"/>' % req.href('captcha.png')
                else:
                    captcha = skimpyAPI.Pre(word).data()
                content = "<p>%s</p><p>%s</p>" % (msg, captcha)
                content += '<label>Confirm: <input type="text" name="captcha" class="textwidget" size="20"/></label>'
                stream |= Transformer('//form[@id="%s"]' % form_id).append(tag.div(Markup(content)))
                #DEBUG
                #stream |= Transformer('//form[@id="%s"]' % form_id).append(tag.div(Markup(word)))

        return stream

    ### method for IRequireComponents

    def requires(self):
        """list of component classes that this component depends on"""
        return [ImageCaptcha]
