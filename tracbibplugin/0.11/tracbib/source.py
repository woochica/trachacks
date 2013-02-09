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
from trac.versioncontrol import RepositoryManager
version = 0.12
if hasattr(RepositoryManager, 'get_repository_by_path') :
    version = 0.12
else :
    version = 0.10

def _extract(text):
    # convert to utf8 and generate a dictionary
    try:
        try:
            strings, entries = bibtexparse.bibtexload(
                unicode(text, "utf-8").splitlines())
        except TypeError:
            strings, entries = bibtexparse.bibtexload(text.splitlines())
    except UnicodeDecodeError:
        raise TracError("A UnicodeDecodeError occured while loading the"
                        "data. Try to save the file in UTF-8 encoding.")
    crossRef = []
    for k, bib in entries.iteritems():
        bibtexparse.replace_abbrev(bib, def_strings)
        bibtexparse.replace_abbrev(bib, strings)
        if bib.get('crossref'):
            crossRef.append(k)
    # merging the entry and its cross-reference into one dictionary
    for k in crossRef:
        if entries[k]['crossref'] in entries:
            ref = entries[entries[k]['crossref']].copy()
            ref.update(entries[k])
            entries[k] = ref
            print entries[k]
    return entries


class BibtexSourceSource(Component):
    """
    This class loads bibtex files from the repository connected to trac.
    """

    implements(IBibSourceProvider)

    #IBibSourceProvider Methods

    def source_type(self):
        return "source"

    def source(self, req, args):
        arg = re.compile(":|@").split(args)

        if len(arg) < 2:
            raise TracError('[[Usage: BibAdd(source:file[@rev])')
        elif len(arg) == 2:
            revision = None
        else:
            revision = arg[2]

        file = arg[1]

        if version < 0.12:
            repos = self.env.get_repository()
            path = file
        else :
            (reponame, repos, path) = RepositoryManager(self.env).get_repository_by_path(file)

        # load the file from the repository
        bib = repos.get_node(path, revision)
        file = bib.get_content()
        text = file.read()

        return _extract(text)

from trac.attachment import Attachment


class BibtexSourceAttachment(Component):
    """
    This class loads bibtex files from wiki attachments.
    """
    implements(IBibSourceProvider)

    def source_type(self):
        return 'attachment'

    def source(self, req, args):
        arg = re.compile(":").split(args)
        if (len(arg) != 2):
            raise TracError('Usage: BibAdd(attachment:[path/to/]file)')

        realm = 'wiki'
        page = None
        file = arg[1]

        path_info = arg[1].split('/', 1)  # greedy! split wikipath and filename

        if len(path_info) > 2:
            raise TracError('Usage: BibAdd(attachment:[path/to/]file)')
        elif len(path_info) == 1:
            file = path_info[0]
            page = req.args.get('page')
            if page is None:  # TODO: clean solution
                page = 'WikiStart'
            bib = Attachment(self.env, realm, page, file)
        elif len(path_info) == 2:
            page = path_info[0]
            file = path_info[1]

            bib = Attachment(self.env, realm, page, file)
        file = bib.open()
        text = file.read()
        file.close()

        return _extract(text)

from trac.wiki.model import WikiPage


class BibtexSourceWiki(Component):
    """
    This class loads bibtex files from wiki code blocks.
    """

    implements(IBibSourceProvider)

    def source_type(self):
        return 'wiki'

    def source(self, req, args):
        arg = re.compile(":").split(args)
        if (len(arg) != 2):
            raise TracError('Usage BibAdd(wiki:page)')
        name = arg[1]
        page = WikiPage(self.env, name)
        if page.exists:
            if '{{{' in page.text and '}}}' in page.text:
                block = re.compile('{{{|}}}', 2).split(page.text)
                text = block[1]
            else:
                raise TracError(
                    'No code block on page \'' + name + '\' found.')
        else:
            raise TracError('No wiki page named \'' + name + '\' found.')

        return _extract(text)

import urllib


class BibtexSourceHttp(Component):
    """
    This class loads bibtex files from external websites.
    """

    implements(IBibSourceProvider)

    def source_type(self):
        return 'http[s]?'

    def source(self, req, args):
        url = args
        try:
            file = urllib.urlopen(url)
            text = file.read()
            file.close()
        except:
            raise TracError('Usage BibAdd(http[s]://url). Is the provided URL'
                            ' correct?')

        return _extract(text)
