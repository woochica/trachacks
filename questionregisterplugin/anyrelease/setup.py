from setuptools import find_packages, setup

setup(
    name = 'TracQuestionRegister',
    version = '0.0.1',
    author = 'Guido Tabbernuk',
    author_email = 'boamaod@gmail.com',
    url = 'http://trac-hacks.org/wiki/QuestionRegisterPlugin',
    description = 'Asks a question while registering, depends on AccountManagerPlugin',
    license = 'GPL',
    packages = find_packages(exclude=['*.tests*']),
    install_requires = [
        'trac>=0.11',
        #'AccountManagerPlugin==0.2.1',
        #'recaptcha_client>=1.0.2',
    ],
    entry_points = {
        'trac.plugins': [
            'questionregister = questionregister.web_ui'
        ]
    },
)
