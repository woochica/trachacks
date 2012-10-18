# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 The Open Planning Project
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from genshi.builder import tag

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket import ITicketChangeListener, Ticket

class TracBacksPlugin(Component):
    implements(ITicketChangeListener)

    TRACBACK_MAGIC_NUMBER = "{{{\n#!html\n<div class=\"tracback\"></div>\n}}}\n"
    TRACBACK_PREFIX = "This ticket has been referenced in ticket #"
    
    TICKET_REGEX = r"""
        (?=                    # Don't return '#' character:
          (?!\{\{\{.*)	       # Exclude comment blocks 
	  (?<=^\#)            # Look for a TracLink Ticket at the beginning of the string
          |(?<=[\s,.;:!]\#)    # or on a whitespace boundary or some punctuation
          |(?<=ticket:)        # or the "ticket:NNN" format
        )
        (?!.*\}\}\})
        (\d+)                  # Any length ticket number (return the digits)
        (?=
           (?=\b)              # Don't return word boundary at the end
          |$                   # Don't return end of string
        )
        """

    EXCERPT_CHARACTERS = 80
    WEED_BUFFER = 2

    # ITicketChangeListener methods

    def ticket_created(self, ticket):
        # Check for tracbacks on ticket creation.
        self.ticket_changed(ticket, ticket.values.get('description'),
                            ticket.values.get('reporter'), None)
        
    def ticket_changed(self, ticket, comment, author, old_values):
        
        pattern = re.compile(self.TICKET_REGEX, re.DOTALL|re.VERBOSE)

        if not isinstance(comment, basestring):
            return
        
        tickets_referenced = pattern.findall(comment)
        # convert from strings to ints and discard duplicates
        tickets_referenced = set(int(t) for t in tickets_referenced)
        # remove possible self-reference
        tickets_referenced.discard(ticket.id)

        # put trackbacks on the tickets that we found
        if not self.is_tracback(comment): # prevent infinite recursion
            for ticket_to_tracback in tickets_referenced:
                try:
                    t = Ticket(self.env, ticket_to_tracback)
                except ResourceNotFound: # referenced ticket does not exist
                    continue
                    
                tracback = self.create_tracbacks(ticket, t, comment)
                
                # cnum is stored in the ticket_change table as an string
                # identifying the comment number, and if applicable,
                # the replyto comment number. If comment 8 is a reply to
                # comment 4, the string will be '4.8'. The index is used
                # by the TicketChangePlugin to identify the comment being
                # edited, so we make sure to add it here.
                change_log = [i for i in t.get_changelog()
                              if i[2] == "comment"]
                if change_log != []:
                    lastchange = change_log[-1]
                    cnum_lastchange = lastchange[3].rsplit('.', 1)
                    cnum_lastcomment = int(cnum_lastchange[-1])
                    cnum_thischange = str(cnum_lastcomment + 1)
                else:
                    cnum_thischange = "1"
                t.save_changes(author, tracback, cnum=cnum_thischange)
                    

    def ticket_deleted(self, ticket):
        pass
        
    def is_tracback(self, comment):
        return comment.startswith(self.TRACBACK_MAGIC_NUMBER)
        
    def create_tracbacks(self, ticket, ticket_to_tracback, comment):
        tracback = self.TRACBACK_MAGIC_NUMBER + self.TRACBACK_PREFIX + str(ticket.id) + ":"
        
        # find all occurrences of ticket_to_tracback. This is error prone.
        # we'll weed the errors out later.
        string_representation = "#" + str(ticket_to_tracback.id)
        
        excerpts = []
        
        index = -1
        while comment.find(string_representation, index + 1) > -1:
            # Get two characters in context so we can make sure this is really
            # a reference to a ticket, and not anything else.
            index = comment.find(string_representation, index + 1)
            
            if not self.is_weed(comment, index, index + len(string_representation)):
                start = index - self.EXCERPT_CHARACTERS
                end = index + len(string_representation) + self.EXCERPT_CHARACTERS  
                    
                left_ellipsis = "..."
                right_ellipsis = "..."
                    
                # Make sure we don't go into the negative. Also, make the ellipsis'
                # disappear if we're not actually cutting up the comment.
                if start <= 0:
                    left_ellipsis = ""
                    start = 0
                
                if end >= len(comment):
                    right_ellipsis = ""
                
                excerpt = comment[start:end]
                excerpt = excerpt.replace("\n", "")
                
                # There's probably a better way to say this in python, but Tim doesn't know
                # how to do it. (He's tried """ but something's foobar'ed.)
                excerpts.append("\n> %s%s%s\n" % (left_ellipsis, excerpt, right_ellipsis))
            
        tracback += ''.join(excerpts)
        return tracback
        
    def is_weed(self, comment, start, end):
        start -= self.WEED_BUFFER
        end += self.WEED_BUFFER
        
        # Make sure we don't have a negative starting value.
        if start < 0:
            start = 0
            
        try:
            match = re.search(self.TICKET_REGEX, comment[start:end])
            return False
        except: # Not a match. This must be a weed.
            return True
        
        
        
        
#        Doug, with some very very cool regular expression prowess, produced
#        the following regular expression that returns sentences with ticket
#        links in them. We could use this -- and almost should -- but I'm 
#        going to use the easy method for now as it takes less expertise.
#        
#        sentence_pattern = r"""
#        (?:                       # This initial group isn't a matching group
#            (?<=\.)               # End of previous sentence is a period
#           |(?<=\.\s)             #     or period with one space
#           |(?<=\.\s\s)           #     or period with two space
#           |(?<=\.\s\s\s)         #     or period with three spaces
#           |(?<=\.\s\s\s\s)       #     or period with four spaces
#           |^                     # Or we match the beginning of the line
#        )
#        (                         # We match everything else and return it
#                                  # Because of this, we don't return any other
#                                  # matches
#                [^\s]             # A sentence does not begin with a space
#                (?:               # Match the beginning of the sentence
#                    [^.]          # A sentence does not contain a period
#                   |\.[^\s]       # unless it's part of a word, like a URL
#                )*                # Match any length
#    
#            (?=                   # Starting here is a duplicate of the ticketlink
#                                  # above, but without returning any text
#               (?<=^\#)           # Look for a TracLink Ticket at the beginning of the string
#              |(?<=[\s,.;:!]\#)   # or on a whitespace boundary or some punctuation
#            )
#            (?=\d+)               # Any length ticket number (return the digits)
#            (?=                   # Don't return the end of the ticke tink
#               (?=\b)             # Whether it's a word boundary
#              |$                  # Or an end of string
#            )
#            (?:                   # Here we match the end of the sentence
#                                  # It follows the same rules as the beginning
#                [^.]              # Don't match a period
#               |\.[^\s]           # unless it's inside a word
#            )*                    # Any length to the end of the sentence
#            (?:                   # Here we will match the end of the sentence
#                (?:\.             # Which is a period (returned as part of the
#                                  # above expression
#                    (?=\s+|$)     # then followed by unmatched whitespace or the
#                                  # end of the line
#                )
#               |$                 # if there's no period, jus tthe end of the line
#                                  # We'll accept that too
#            )
#        )
#        """
#        excerpt = re.compile(sentence_pattern, re.VERBOSE | re.MULTILINE)
