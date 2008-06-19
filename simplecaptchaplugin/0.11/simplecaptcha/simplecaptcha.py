"""
A simple captcha for use with AccountManagerPlugin

You should edit trac.ini to point to your captcha dictionray file.
"""
import random
import sys
import time
import urllib

from skimpyGimpy import skimpyAPI

from trac.core import *
from trac.config import PathOption

from acct_mgr.api import IRegistrationConfirmation

class SimplecaptchaPlugin(Component):
    implements(IRegistrationConfirmation)

    dict_file = PathOption('simplecaptcha', 'dictionary_file',
                           default="http://java.sun.com/docs/books/tutorial/collections/interfaces/examples/dictionary.txt")

    def __init__(self):
        self.keys = {}

    def pre_registration(self, req):
        """ Returns the HTML to be added to the registration form """
        msg = "Please enter the text below to prove you're not a machine."
        key = random.Random().randint(0, sys.maxint)
        word = self._random_word()
        self.keys[key] = (word, time.time())
        
        content = "<div><p>%s</p>%s" % (msg, self._get_captcha(word))
        content += "<label>Enter Word: <input type='text' name='simplecaptcha_captcha' class='textwidget' size='20'></label>"
        content += "<input type='hidden' name='simplecaptcha_key' value='%s' /></div>" % key
        
        return content

    def verify_registration(self, req):
        """Returns an error message if confirmation fails, or None on success
        """
        # keys older than 10min get deleted
        timeout = 600
        [self.keys.pop(k) for k, (word, timestamp) in self.keys.items() 
         if time.time()-timestamp >= timeout]

        key = int(req.args['simplecaptcha_key'])
        if not self.keys.has_key(key): # timeout
            return req.redirect(req.href.base + "/register")
        correct_answer, timestamp = self.keys.pop(key)
        if req.args['simplecaptcha_captcha'].lower() != correct_answer:
            return "Sorry, the word you entered was incorrect. Please try again."

        return None

    def _random_word(self):
        """Returns a random word for use with the captcha"""
        min_len =  5
        
        if not globals().has_key('captcha_dict'):
            if self.dict_file.startswith("http://"):
                f = urllib.urlopen(self.dict_file)
            else:
                f = open(self.dict_file, "r")
            _dict = f.read()
            f.close()    
            _dict = _dict.lower().split()
            _dict = [word for word in _dict if word.isalpha() and len(word) > min_len]
            globals()['captcha_dict'] = _dict

        return random.Random().choice(captcha_dict)

    def _get_captcha(self, passphrase):
        """Returns HTML content of captcha as string"""
        return skimpyAPI.Pre(passphrase).data()
