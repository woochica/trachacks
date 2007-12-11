"""
This file contains structures used to create question form
which must user fill up before he can download any file.

FORBIDEN NAMES: nr, id, timestamp, file_id, file_name
"""      
quest_form = [
    {
        'type': 'text',
        'name': 'name',
        'label': 'Name:',
        'show_in_main_list': True,
        'regexp': r'.*\w{2}.*',
        'errinfo': 'Name must be at least 2 characters long.'
    },
    {
        'type': 'text',
        'name': 'surname',
        'label': 'Surname:',
        'show_in_main_list': True,
        'regexp': r'.*\w{2}.*',
        'errinfo': 'Surname must be at least 2 characters long.'
    },
    {
        'type': 'text',
        'name': 'email',
        'label': 'E-mail:',
        'description': 'Valid e-mail address.',
        'show_in_main_list': True,
        'regexp': r'\S*@\S*\.\S*',
        'errinfo': 'You must enter valid e-mail address.'
    },
    {
        'type': 'label',
        'text': 'Purpose:',
        'label_for': 'purpose'
    },
    {
        'type': 'radio',
        'name': 'purpose',
        'cat': 'purpose',
        'value': 'private',
        'label': 'Private',
        'errinfo': 'You must specify purpose of your download.',
        'mustchoose': True
    },
    {
        'type': 'radio',
        'name': 'purpose',
        'cat': 'purpose',
        'value': 'school',
        'label': 'School'
    },
    {
        'type': 'text',
        'name': 'purpose_shool_which',
        'cat': 'purpose',
        'label': 'Which school:'
    },
    {
        'type': 'radio',
        'name': 'purpose',
        'cat': 'purpose',
        'value': 'commercial',
        'label': 'Commercial',
        'last': True
    },
    {
        'type': 'text',
        'name': 'purpose_commercial_which',
        'cat': 'purpose',
        'label': 'Which company:'
    },
    {
        'type': 'checkb',
        'name': 'crazy',
        'value': 'yes',
        'label': 'I\'m crazy!'
    },
]
