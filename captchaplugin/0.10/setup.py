from setuptools import setup

setup(name='TracCaptcha',
      version='0.1',
      packages=['traccaptcha'],
      author='Alec Thomas',
      url='http://trac-hacks.org/wiki/CaptchaPlugin',
      license='BSD',
# This doesn't seem to work for me? I suspect PIL needs to be installed with
# setuptools.
#      extras_require = {
#        'PIL': ['PIL>=1.1.0'],
#      },
      entry_points = """
        [trac.plugins]
        traccaptcha = traccaptcha
        traccaptcha.expression = traccaptcha.expression
        traccaptcha.image = traccaptcha.image
        traccaptcha.captchadotnet = traccaptcha.captchadotnet
      """,
      package_data={'traccaptcha' : ['templates/*.cs', 'fonts/*.ttf']})
