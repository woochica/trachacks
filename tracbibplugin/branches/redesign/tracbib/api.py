"""
 tracbib/api.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.

 This file contains all Interfaces to customize tracbib with new cite formats
 and new BibTex source containers.

 tracbib is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 tracbib is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with tracbib.  If not, see <http://www.gnu.org/licenses/>.
"""

from trac.core import Interface

class IBibSourceProvider(Interface):

    def source_type():
        """return the keyword to identify the source of the bibtex entries"""

    def source_init(req, args):
        """do what ever you have to do to initialize the source"""

    # these methods can be derived from 'dict'

    def clear():
        """delete all previously loaded or cached entries, only do this if it is
        necessary to avoid sideffects. This is especially usefull if the
        entries are loaded from static files at once."""

    def has_key(key):
        """ckeck if the specified key is in the library """

    def __iter__():
        """return iterator"""

    def __getitem__(key):
        """return the dictionary of the entries of the specified key """

    def items():
        """return items [(key,value),...] """


class IBibRefFormatter(Interface):

    def formatter_type():
        """return the keyword to identify the format style"""

    def format_ref(entries,label):
        """returns a fully formated list of all cited entries"""

    def format_fullref(entries,label):
        """returns a fully formated list of all loaded entries"""

    def format_cite(key,entry):
        """returns a fully formated citation"""

    def pre_process_entry(key,cite):
        """use this extension point to store formatting information if you have
        to, e.g. for final sorting."""
