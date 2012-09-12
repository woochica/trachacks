# -*- coding: utf-8 -*-

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
