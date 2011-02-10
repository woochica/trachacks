from setuptools import find_packages, setup

setup(
    name = 'TracRecaptchaRegister',
    version = '0.2.1.2',
    author = 'Alejandro J. Cura',
    author_email = 'alecu@vortech.com.ar',
    url = 'http://trac-hacks.org/wiki/RecaptchaRegisterPlugin',
    description = 'Adds a recaptcha while registering, depends on AccountManagerPlugin',
    license = 'GPL',
    packages = find_packages(exclude=['*.tests*']),
    package_data = {'recaptcharegister': ['templates/*.cs']},
    install_requires = [
        #'trac>=0.11',
        #'AccountManagerPlugin==0.2.1',
        'recaptcha_client>=1.0.2',
    ],
    entry_points = {
        'trac.plugins': [
            'recaptcharegister = recaptcharegister.web_ui'
        ]
    },
)
