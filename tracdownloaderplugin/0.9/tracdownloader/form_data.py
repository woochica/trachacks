# -*- coding: utf-8 -*-
#
# Author: Petr Škoda <pecast_cz@seznam.cz>
# All rights reserved.
#
# This software is licensed under GNU GPL. You can read  it at
# http://www.gnu.org/licenses/gpl-3.0.html
#

"""
This file contains structures used to create question form
which must user fill up before he can download any file.

Each part like the one bottom represnts one item in questionnaire.
    {
        'type': 'text',
        'name': 'name',
        'label': 'Name:',
        'show_in_main_list': True,
        'regexp': r'.*\w{2}.*',
        'errinfo': 'Name must be at least 2 characters long.'
    },

ATTRIBUTES:
    type:
        text    gives <input type="text" />
                MEANINGFUL CO-ATTRIBUTES:
                    name
                    label
                    show_in_main_list
                    regexp
                    errinfo
                    cat
        radio   gives <input type="radio" />
                MEANINGFUL CO-ATTRIBUTES:
                    name
                    label
                    value
                    show_in_main_list
                    mustchoose (only first of same name)
                    errinfo (only first of same name)
                    cat
        checkb  gives <input type="checkbox" />
                MEANINGFUL CO-ATTRIBUTES:
                    name
                    label
                    value
                    show_in_main_list
        label   gives just text label into questionnaire (good for radios)
                MEANINGFUL CO-ATTRIBUTES:
                    text
                    label_for
    
    name        Should be unique for each element in questionnaire, it's used
                to reference it.
    label       Is text displayed to user about that item input questionnaire
                for example text above text input, or text on right side of 
                radio and checkbox.
    value       Is value of radio or checkbox which will be saved if that
                item is checked.
    regexp      It's standard regular expression, this string should be signed 
                with r before it like r'regular expression'. Documentation about 
                Python regex is at http://docs.python.org/lib/re-syntax.html.
                For example if you want check only lenght of given string
                you can use regex like this: r'.*\w{2}.*' It says that correct 
                is non whitespace value longer than 2 letters.
    errinfo     This is the text given to user if he filled particular field 
                incorrectly. It depends on regex for type text and on 
                mustchoose for type radio.
    mustchoose  You can set this to True in the first item of radio choose to
                foce user choose one of radios with that name.
    cat         This is only for organisation, if you give the same cat for
                few elements one after another, they will be separated by
                space before and after whole category - good for radio and
                checkb.
    label_for   Set this in type of label to name of some category 
                (it's recomanded to cathegrorize radios and checkboxes) and this
                label will be shown at admin stats as name of this item when
                showing questionnaire fill up. If you don't use this, the name 
                of radio will be taken from label of first radio input set.
    show_in_main_list
                If this is set to True, this item will be displayed input table
                on Stats admin page, so you can easily browse and sort it's
                values.


FORBIDDEN NAMES: nr, id, timestamp, file_id, file_name
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
        'mustchoose': True,
        'show_in_main_list': True,
    },
    {
        'type': 'radio',
        'name': 'purpose',
        'cat': 'purpose',
        'value': 'school',
        'label': 'School',
    },
    {
        'type': 'text',
        'name': 'purpose_shool_which',
        'cat': 'purpose',
        'label': 'Which school:',
    },
    {
        'type': 'radio',
        'name': 'purpose',
        'cat': 'purpose',
        'value': 'commercial',
        'label': 'Commercial',
        'last': True,
    },
    {
        'type': 'text',
        'name': 'purpose_commercial_which',
        'cat': 'purpose',
        'label': 'Which company:',
    },
]
