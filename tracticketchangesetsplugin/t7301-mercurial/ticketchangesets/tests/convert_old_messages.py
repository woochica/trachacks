# This is not a test module in the normal sense, but merely a hacking corner
# to create and verify some tricky code fragments which have been pasted into
# the installation code. This module is kept for the purposes of further
# development.

# TODO: Create a real test environment.

from ticketchangesets.admin import _reformat_message

# [("message", "converted message")]
testmessages = [
    #1 -- Message created by old custom script by mrelbe for Trac 0.11.x:
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

    #3 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater):
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

    #4 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater):
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

    #5 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at end
    #  -- Old
    ("""\
In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}Manual edit line 1""",
    #  -- New
    """\
[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}

Manual edit line 1"""),

    #6 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at end
    #  -- Old
    ("""\
In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}


Manual edit line 1

""",
    #  -- New
    """\
[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}

Manual edit line 1"""),

    #7 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at end
    #  -- Old
    ("""\
In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}Manual edit line 1
Manual edit line 2""",
    #  -- New
    """\
[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}

Manual edit line 1
Manual edit line 2"""),

    #8 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at start
    #  -- Old
    ("""\
Manual edit line 1 In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}""",
    #  -- New
    """\
Manual edit line 1

[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}"""),

    #9 -- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at start
    #  -- Old
    ("""\
Manual edit line 1

In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}""",
    #  -- New
    """\
Manual edit line 1

[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}"""),

    #10-- Message created by Trac 0.12 (tracopt.ticket.commit_updater)
    #     with manually added comment at both start and end
    #  -- Old
    ("""\
Manual edit line 1
Manual edit line 2
In [234]:
{{{
#!CommitTicketReference repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}
Manual edit line 1
Manual edit line 2""",
    #  -- New
    """\
Manual edit line 1
Manual edit line 2

[234/reponame]:
{{{
#!CommitMessage repository="reponame" revision="234"
Committing to repo for testing ticket commit updater, see #61

End...
}}}

Manual edit line 1
Manual edit line 2"""),

]


def test():
    """Replace old commit messages with new."""
    n = 0
    for oldmessage, expectednewmessage in testmessages:
        n += 1
        newmessage = _reformat_message(oldmessage)
        if newmessage:
            if newmessage == expectednewmessage:
                print('Test %d Ok' % n)
            else:
                print("""
Test %d FAILED!
---- Old message ----
%s
---------------------
---- New message ----
%s
--------------------------
---- Expected message ----
%s
--------------------------
""" % (n, oldmessage, newmessage, expectednewmessage))
                raise ValueError
            continue
        if oldmessage == expectednewmessage:
            print('Test %d OK' % n)
        else:
            print('Test %d FAIL' % n)
            print('Old message:\n%s' % oldmessage)
            print('New message:\n%s' % newmessage)
            raise ValueError

test()
