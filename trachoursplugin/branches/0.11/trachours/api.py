# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Jeff Hammel <jhammel@openplans.org>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

hours_format = '%.2f'

custom_fields = { 'estimatedhours': 
                  { 'type': 'text',
                    'label': 'Estimated Hours',
                    'value': '0' 
                    },
                  'totalhours':
                      { 'type': 'text', # should be a computed field, 
                        # but computed fields don't yet exist for trac
                        'label': 'Total Hours',
                        'value': '0'
                        }
                  }
