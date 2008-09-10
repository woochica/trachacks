from acct_mgr.web_ui import RegistrationModule
from trac.web.main import IRequestHandler, IRequestFilter
from trac.config import ConfigurationError, Option
from recaptcha.client import captcha


class RecaptchaRegistrationModule(RegistrationModule):
    public_key = Option('recaptcha', 'public_key',
        doc='The public key given to you from the reCAPTCHA site')
    private_key = Option('recaptcha', 'private_key',
        doc='The private key given to you from the reCAPTCHA site')

    def check_config(self):
        if not self.public_key or not self.private_key:
            raise ConfigurationError('public_key and private_key needs ' \
                'to be in the [captcha] section of your trac.ini file. ' \
                'Get these keys from http://recaptcha.net/')

    # IRequestHandler methods
    def process_request(self, req):
        self.check_config()
        action = req.args.get('action')

        if req.method == 'POST' and action == 'create':
            response = captcha.submit(
                req.args['recaptcha_challenge_field'],
                req.args['recaptcha_response_field'],
                self.private_key,
                req.remote_addr,
                )
            if not response.is_valid:
                data = {}
                data['registration_error'] = 'Captcha incorrect. Please try again.'
                data['recaptcha_javascript'] = captcha.displayhtml(self.public_key)
                return "recaptcharegister.html", data, None
            else:
                ret = super(RecaptchaRegistrationModule, self).process_request(req)
                h, data, n = ret
                return "recaptcharegister.html", data, n
        else:
            ret = super(RecaptchaRegistrationModule, self).process_request(req)
            h, data, n = ret
            data['recaptcha_javascript'] = captcha.displayhtml(self.public_key)
            return "recaptcharegister.html", data, n

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
