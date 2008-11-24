"""
model.py

====================

Copyright (C) 2008 Roel Harbers

 ----------------------------------------------------------------------------
 "THE BEER-WARE LICENSE" (Revision 42):
 Roel Harbers wrote this file. As long as you retain this notice you
 can do whatever you want with this stuff. If we meet some day, and you think
 this stuff is worth it, you can buy me a beer in return.
 ----------------------------------------------------------------------------

Description:

  This module contains model classes for regexlinkplugin.

Author:

  Roel Harbers

"""
import re

class RegexLinkInfo:

    def __init__(self, regex, url):
        self.regex = regex
        self.url = url

    def replace_url(self, match):
        """ perform regex substitution on url using match data object
        """
        return re.sub(self.regex, self.url, match.group(0))
