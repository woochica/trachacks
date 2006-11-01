import os
import random
import Image
import ImageFont
import ImageDraw
import ImageFilter
from StringIO import StringIO
from trac.core import *
from trac.util.html import html
from trac.config import *
from traccaptcha import ICaptchaGenerator
from trac.web.api import IRequestHandler


def gen_captcha(file, text, fnt, fnt_sz, fmt='JPEG'):
    # randomly select the foreground color
    fgcolor = random.randint(0,0xffff00)
    # make the background color the opposite of fgcolor
    bgcolor = fgcolor ^ 0xffffff
    # create a font object 
    font = ImageFont.truetype(fnt,fnt_sz)
    # determine dimensions of the text
    dim = font.getsize(text)
    # create a new image slightly larger that the text
    im = Image.new('RGB', (dim[0]+5,dim[1]+5), bgcolor)
    d = ImageDraw.Draw(im)
    x, y = im.size
    r = random.randint
    # draw 100 random colored boxes on the background
    for num in range(100):
        d.rectangle((r(0,x),r(0,y),r(0,x),r(0,y)),fill=r(0,0xffffff))
    # add the text to the image
    d.text((3,3), text, font=font, fill=fgcolor)
    im = im.filter(ImageFilter.EDGE_ENHANCE_MORE)
    # save the image to a file
    im.save(file, format=fmt)


class ImageCaptcha(Component):
    """ An image captcha courtesy of
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/440588 """

    implements(ICaptchaGenerator)
    implements(IRequestHandler)

    fonts = ListOption('image-captcha', 'fonts', 'vera.ttf',
        """ Set of fonts to choose from. """)
    font_size = IntOption('image-captcha', 'font_size', 25)
    alphabet = Option('image-captcha', 'alphabet', 'abcdefghkmnopqrstuvwxyz',
        """ Alphabet to choose captcha challenge from. """)
    letters = IntOption('image-captcha', 'letters', 6,
        """ Number of letters to use in challenge. """)

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/captcha/image'

    def process_request(self, req):
        if 'captcha_expected' not in req.session:
            # TODO Probably need to render an error image here
            raise TracError('No Captcha response in session')
        req.send_response(200)
        req.send_header('Content-Type', 'image/jpeg')
        req.end_headers()

        image = StringIO()
        from pkg_resources import resource_filename
        font = os.path.join(resource_filename(__name__, 'fonts'),
                            random.choice(self.fonts))
        gen_captcha(image, req.session['captcha_expected'], font,
                    self.font_size)
        req.write(image.getvalue())

    # ICaptchaGenerator methods
    def generate_captcha(self, req):
        challenge = ''.join([random.choice(self.alphabet) for _ in xrange(self.letters)])
        return challenge, html.p('Please respond with the letters in the following image:') + \
                          html.blockquote(html.img(src=req.href('/captcha/image')))
