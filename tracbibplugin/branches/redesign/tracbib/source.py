"""
 tracbib/source.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.

 This file provides support for loading bibtex files from the version control
 system, from a wiki page or a wiki attachment.

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

"""
This class provides different container implementations of bibtex files.
"""
from api import IBibSourceProvider
from trac.core import implements, Component, TracError

import bibtexparse
from helper import def_strings
import re

class BibtexSourceBase(dict):
    """
    The bibtex base class handles the utf-8 conversion and the bibtex parsing.
    """

    def extract(self,text):
        # convert to utf8 and generate a dictionary
        try:
            try:
                strings,entries=bibtexparse.bibtexload(unicode(text,"utf-8").splitlines());
            except TypeError:
                strings,entries=bibtexparse.bibtexload(text.splitlines());
        except UnicodeDecodeError:
            raise TracError("A UnicodeDecodeError occured while loading the data. Try to save the file in UTF-8 encoding.")
        crossRef = []
        for k,bib in entries.iteritems():
            bibtexparse.replace_abbrev(bib, def_strings)
            bibtexparse.replace_abbrev(bib,strings)
            if bib.get('crossref'):
                crossRef.append(k)
        self.update(entries)
        # merging the entry and its cross-reference into one dictionary
        for k in crossRef:
            if self.has_key(self[k]['crossref']):
                ref = self[self[k]['crossref']].copy()
                ref.update(self[k])
                self[k]=ref 
                print self[k]

class BibtexSourceSource(Component): 
    """
    This class loads bibtex files from the repository connected to trac.
    """

    implements(IBibSourceProvider)
    bibtex = BibtexSourceBase()

    #IBibSourceProvider Methods

    def source_type(self):
        return "source"

    def source_init(self,req,args):
        arg = re.compile(":|@").split(args)

        if len(arg) < 2:
            raise TracError('[[Usage: BibAdd(source:file[@rev])')
        elif len(arg) == 2:
            revision = 'latest'
        else:
            revision = arg[2]

        file = arg[1]

        repos = self.env.get_repository()

        # load the file from the repository 
        bib = repos.get_node(file, revision)
        file = bib.get_content()
        text = file.read()

        self.bibtex.extract(text)

    def has_key(self,key):
        return self.bibtex.has_key(key)

    def clear(self):
        self.bibtex.clear()

    def __iter__(self):
        return self.bibtex.__iter__()

    def __getitem__(self,key):
        return self.bibtex.__getitem__(key);

    def items(self):
        return self.bibtex.items()



from trac.attachment import Attachment

class BibtexSourceAttachment(Component):
    """
    This class loads bibtex files from wiki attachments.
    """
    bibtex = BibtexSourceBase()

    implements(IBibSourceProvider)
   

    def source_type(self):
        return 'attachment'

    def source_init(self,req,args):
        arg = re.compile(":").split(args)
        if (len(arg) != 2):
            raise TracError('Usage: BibAdd(attachment:[path/to/]file)')

        realm = 'wiki'
        page = None
        file = arg[1]

        path_info = arg[1].split('/',1) # greedy! split wikipath and filename

        if len(path_info) > 2:
            raise TracError('Usage: BibAdd(attachment:[path/to/]file)')
        elif len(path_info) == 1:
            file = path_info[0]
            page= req.args.get('page')
            if page == None: # TODO: clean solution
                page = 'WikiStart'
            bib = Attachment(self.env,realm,page,file)
        elif len(path_info) == 2:
            page = path_info[0]
            file = path_info[1]

            bib = Attachment(self.env,realm,page,file)
        file = bib.open()
        text = file.read()
        file.close()

        self.bibtex.extract(text)

    def has_key(self,key):
        return self.bibtex.has_key(key)

    def clear(self):
        self.bibtex.clear()

    def __iter__(self):
        return self.bibtex.__iter__()

    def __getitem__(self,key):
        return self.bibtex.__getitem__(key);

    def items(self):
        return self.bibtex.items()


from trac.wiki.model import WikiPage

class BibtexSourceWiki(Component):
    """
    This class loads bibtex files from wiki code blocks.
    """

    implements(IBibSourceProvider)
    bibtex = BibtexSourceBase()

    def source_type(self):
        return 'wiki'

    def source_init(self,req,args):
        arg = re.compile(":").split(args)
        if (len(arg) != 2):
            raise TracError('Usage BibAdd(wiki:page)')
        name = arg[1]
        page = WikiPage(self.env,name)
        if page.exists:
            if '{{{' in page.text and '}}}' in page.text:
                block = re.compile('{{{|}}}',2).split(page.text)
                text = block[1]
            else:
                raise TracError('No code block on page \'' + name + '\' found.')
        else:
          raise TracError('No wiki page named \'' + name + '\' found.')

        self.bibtex.extract(text)

    def has_key(self,key):
        return self.bibtex.has_key(key)

    def clear(self):
        self.bibtex.clear()

    def __iter__(self):
        return self.bibtex.__iter__()

    def __getitem__(self,key):
        return self.bibtex.__getitem__(key);

    def items(self):
        return self.bibtex.items()

import urllib

class BibtexSourceAttachment(Component):
    """
    This class loads bibtex files from external websites.
    """
    bibtex = BibtexSourceBase()

    implements(IBibSourceProvider)
   

    def source_type(self):
        return 'http'

    def source_init(self,req,args):
        url = args
        try:
            file = urllib.urlopen(url)
            text = file.read()
            file.close()
        except:
            raise TracError('Usage BibAdd(http://url)')

        self.bibtex.extract(text)

    def has_key(self,key):
        return self.bibtex.has_key(key)

    def clear(self):
        self.bibtex.clear()

    def __iter__(self):
        return self.bibtex.__iter__()

    def __getitem__(self,key):
        return self.bibtex.__getitem__(key);

    def items(self):
        return self.bibtex.items()



