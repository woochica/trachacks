import re

from trac.util.compat import any

from ticketchangesets.commit_updater import make_ticket_comment

# [("message", "converted message")]
testmessages = [
    #1
    ("""\
{{{
#!div class="ticket-commit-message"
[232]:
project-sites/trac/share: Added InterTrac link Sales, and alias SM, for all project sites. See #59
}}}""",
     """\
[232]:
{{{
#!CommitMessage revision="232"
project-sites/trac/share: Added InterTrac link Sales, and alias SM, for all project sites. See #59
}}}"""),

    #2 (not converted)
    ("""\
[229]:
{{{
#!CommitMessage revision="229"
project-sites/scripts: Adjusted for new server (re #41)
}}}""",
    """\
[229]:
{{{
#!CommitMessage revision="229"
project-sites/scripts: Adjusted for new server (re #41)
}}}"""),

    #3
    ("""\
In [234]:
{{{
#!CommitTicketReference repository="" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}""",
    """\
[234]:
{{{
#!CommitMessage revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}"""),

    #4
    ("""\
In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}""",
    """\
[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}"""),
]


def test():
    """Replace old commit messages with new."""

    # Old message patterns and extract functions.
    # Lambda function applied when ticket message matches pattern,
    # extracted tuple: (reponame, rev, message)
    oldmessage_pat = [
        # Message created by Trac 0.12 (tracopt.ticket.commit_updater):
        (r'^In \[.*?\]:\s+{{{\s*#!CommitTicketReference\s+'
         r'repository="(?P<reponame>.*?)"\s+revision="(?P<rev>[0-9]+)"\s+'
         r'(?P<message>.*?)\s+}}}$',
         lambda extract: (extract[0], extract[1], extract[2])),
        # Message created by old custom script by mrelbe for Trac 0.11.x:
        (r'^{{{\s*#!div class="ticket-commit-message"\s+'
         r'\[(?P<rev>[0-9]+)\]:\s+(?P<message>.*?)\s+}}}$',
         lambda extract: ("", extract[0], extract[1])),
    ]
    oldmessage_re = [(re.compile(pat, re.DOTALL), extract) for pat, extract in
                     oldmessage_pat]
    
    n = 0
    for oldmessage, expectednewmessage in testmessages:
        n += 1
        matches = [(parts[0], extract) for parts, extract in 
                [(pat.findall(oldmessage), extract) for pat, extract in
                 oldmessage_re] if parts]
        if matches:
            parts, extract = matches[0]
            reponame, rev, message = extract(parts)

            newmessage = make_ticket_comment(rev, message, reponame)

            if newmessage == expectednewmessage:
                print('Test %d Ok' % n)
            else:
                print('Test %d FAIL!' % n)
                print
                print('Old message:\n%s' % oldmessage)
                print
                print('New message:\n%s' % newmessage)
                print
                print('Expected message:\n%s' % expectednewmessage)
                print
                raise ValueError
            continue
        if oldmessage == expectednewmessage:
            print('Test %d Ok' % n)
        else:
            print('FAIL!')
            print('Old message:\n%s' % oldmessage)
            print('New message:\n%s' % newmessage)
            raise ValueError

test()
