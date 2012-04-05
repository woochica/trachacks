#!/usr/bin/python
#
# Test program for the multiprojectcommitticketupdater plugin to Trac.
#
# Ruth Trevor-Allen, NAG Oxford, 2011.
import sys 
sys.path.append('..') 

from multicommitupdater.commitupdater import MultiProjectCommitTicketUpdater
import trac.env
import time, unittest
from trac.core import ComponentManager
from trac.versioncontrol.api import Repository, Changeset

class TestMultiProjectCommitTicketUpdater(unittest.TestCase):
    # Component architecture plumbing - load environments and components
    # under test (check that each environment matches the right tickets)
    comp_mgr1 = trac.env.open_environment('./testenv/')
    comp_mgr2 = trac.env.open_environment('./testenv2/')
    obj1 = MultiProjectCommitTicketUpdater(comp_mgr1)
    obj2 = MultiProjectCommitTicketUpdater(comp_mgr2)
    # Create fake repository for changesets (note that both fake projects
    # need to use the same fake repository)
    test_repo = Repository("Test_repo",{'name': "Test_repo", 'id': 4321},"tmp.log")

    def setUp(self):
        # Set all component objects to defaults
        self.obj1.config.set("multicommitupdater","envelope","")
        self.obj2.config.set("multicommitupdater","envelope","")
        self.obj1.config.set("multicommitupdater","commands.close",
                             "close closed closes fix fixed fixes")
        self.obj2.config.set("multicommitupdater","commands.close",
                             "close closed closes fix fixed fixes")
        self.obj1.config.set("multicommitupdater","commands.refs",
                             "addresses re references refs see")
        self.obj2.config.set("multicommitupdater","commands.refs",
                             "addresses re references refs see")


    def test_simple_case(self):
        message = "Fixed some stuff. Re test:#1, closes test2:#2"
        test_changeset = Changeset(None,1234,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset)
        # For each object in turn:
        # Get tickets and commands
        tickets = self.obj1._parse_message(message)
        # First, check we've got the tickets we were expecting
        self.assertEqual(tickets.keys(),[1])
        # Now check the actions are right
        self.assertEqual(tickets.get(1),[self.obj1.cmd_refs])
        # Same checks for obj2:
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[2])
        self.assertEqual(tickets.get(2),[self.obj2.cmd_close])

    def test_erroneous_capital_letters(self):
        message = "Did some more stuff. Fixes Test:#3, refs test2:#4"
        test_changeset2 = Changeset(None,1235,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset2)

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[3])
        self.assertEqual(tickets.get(3),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[4])
        self.assertEqual(tickets.get(4),[self.obj2.cmd_refs])

    def test_all_documented_synonyms_close(self):
        message = "More things. close test:#5, closed test2:#6, closes " + \
            "test:#7, fix test2:#8, fixed test:#9, fixes test2:#10."
        test_changeset3 = Changeset(None,1236,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset3)

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[5,7,9])
        self.assertEqual(tickets.get(5),[self.obj1.cmd_close])
        self.assertEqual(tickets.get(7),[self.obj1.cmd_close])
        self.assertEqual(tickets.get(9),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[6,8,10])
        self.assertEqual(tickets.get(6),[self.obj2.cmd_close])
        self.assertEqual(tickets.get(8),[self.obj2.cmd_close])
        self.assertEqual(tickets.get(10),[self.obj2.cmd_close])

    def test_all_documented_synonyms_ref(self):
        message = "Yet more things. references test:#11, refs test2:#12, " + \
            "addresses test:#13, re test2:#14, see test:#15"
        test_changeset4 = Changeset(None,1237,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset4)

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[11,13,15])
        self.assertEqual(tickets.get(11),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(13),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(15),[self.obj1.cmd_refs])

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[12,14])
        self.assertEqual(tickets.get(12),[self.obj2.cmd_refs])
        self.assertEqual(tickets.get(14),[self.obj2.cmd_refs])

# TODO: def test_all_synonyms_ticket(self):

    def test_multiple_tickets_one_command_simple(self):
        message = "And even more things. re test:#16,#17,#18. Closes " + \
            "test2:#19,#20"
        test_changeset5 = Changeset(None,1238,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset5)

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[16,17,18])
        self.assertEqual(tickets.get(16),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(17),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(18),[self.obj1.cmd_refs])

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[19,20])
        self.assertEqual(tickets.get(19),[self.obj2.cmd_close])
        self.assertEqual(tickets.get(20),[self.obj2.cmd_close])

    def test_multiple_tickets_one_command_complex(self):
        message = "Woo, even more things. Look at us go! Refs test:#21 & " + \
            "#22, closes test:#23. See test2:#24,#25 and #26."
        test_changeset6 = Changeset(None,1239,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset6)

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[21,22,23])
        self.assertEqual(tickets.get(21),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(22),[self.obj1.cmd_refs])
        self.assertEqual(tickets.get(23),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[24,25,26])
        self.assertEqual(tickets.get(24),[self.obj2.cmd_refs])
        self.assertEqual(tickets.get(25),[self.obj2.cmd_refs])
        self.assertEqual(tickets.get(26),[self.obj2.cmd_refs])

    def test_one_env(self):
        message = "These things are only applicable to test2. See test" + \
            "2:#27, closes test2:#28"
        test_changeset7 = Changeset(None,1240,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset7)

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets,{})

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[27,28])
        self.assertEqual(tickets.get(27),[self.obj2.cmd_refs])
        self.assertEqual(tickets.get(28),[self.obj2.cmd_close])

    def test_spaces(self):
        message = "Today I am feeling spacey! Closes test:#29, #30. See " + \
            "test2:#31"
        test_changeset8 = Changeset(None,1241,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset8)

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[29,30])
        self.assertEqual(tickets.get(29),[self.obj1.cmd_close])
        self.assertEqual(tickets.get(30),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[31])
        self.assertEqual(tickets.get(31),[self.obj2.cmd_refs])

    #
    # Tests of other documented committicketupdater functionality
    #
    def test_envelope(self):
        message = "Today, I shall be putting my messages in an envelope. " + \
            "[re test:#32], [re test2:#33]"
        test_changeset9 = Changeset(None,1242,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset9)

        # With no envelope set, this works as normal
        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[32])
        self.assertEqual(tickets.get(32),[self.obj1.cmd_refs])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[33])
        self.assertEqual(tickets.get(33),[self.obj2.cmd_refs])

        # With a different envelope set, the messages should be ignored
        self.obj1.config.set("multicommitupdater","envelope","{}")
        self.obj2.config.set("multicommitupdater","envelope","<>")

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

        # Changing one envelope to '[]' should mean only that environment
        # picks up the message
        self.obj1.config.set("multicommitupdater","envelope","[]")

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[32])
        self.assertEqual(tickets.get(32),[self.obj1.cmd_refs])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

        # When both envelopes are '[]', both environments pick up the actions
        self.obj2.config.set("multicommitupdater","envelope","[]")
        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[32])
        self.assertEqual(tickets.get(32),[self.obj1.cmd_refs])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[33])
        self.assertEqual(tickets.get(33),[self.obj2.cmd_refs])

    def test_custom_commands_close(self):
        message = "this time, we're going to use some close commands that " + \
            "aren't on the default list. Nukes test:#34, #35 and " + \
            "obliterates test2:#36"
        test_changeset10 = Changeset(None,1243,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset10)
        
        # Nothing happens if we stick with the default commands
        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

        # Adding 'nukes' to the list should make our first command work
        self.obj1.config.set("multicommitupdater","commands.close",
                             "ends nukes completes")
        self.obj2.config.set("multicommitupdater","commands.close",
                             "ends nukes completes")

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[34,35])
        self.assertEqual(tickets.get(34),[self.obj1.cmd_close])
        self.assertEqual(tickets.get(35),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

        # And adding 'obliterates' should take care of the second
        self.obj1.config.set("multicommitupdater","commands.close",
                             "ends nukes obliterates completes")
        self.obj2.config.set("multicommitupdater","commands.close",
                             "ends nukes obliterates completes")

        tickets = self.obj1._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[34,35])
        self.assertEqual(tickets.get(34),[self.obj1.cmd_close])
        self.assertEqual(tickets.get(35),[self.obj1.cmd_close])

        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[36])
        self.assertEqual(tickets.get(36),[self.obj2.cmd_close])

        # Sad path test
        message = "now we're checking that tickets aren't closed by " + \
            "default commands when the list has been overwritten. " + \
            "closes test:#37, fixes test2:#38"
        test_changeset11 = Changeset(None,1244,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset11)

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

    def test_custom_commands_refs(self):
        message = "And now something very similar wth refs. Lookit test:#39" + \
            "affects test2:#40 & #41"
        test_changeset12 = Changeset(None,1245,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset12)
        
        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

        self.obj1.config.set("multicommitupdater","commands.refs",
                             "relevant-to lookit affects related")
        self.obj2.config.set("multicommitupdater","commands.refs",
                             "relevant-to lookit affects related")

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[39])
        self.assertEqual(tickets.get(39),[self.obj1.cmd_refs])

        tickets = self.obj2._parse_message(message)
        sorted_keys = tickets.keys()
        sorted_keys.sort()
        self.assertEqual(sorted_keys,[40,41])
        self.assertEqual(tickets.get(40),[self.obj2.cmd_refs])
        self.assertEqual(tickets.get(41),[self.obj2.cmd_refs])

        # :(
        message = "can we still ref tickets using one of the old " + \
            "commands? re test:#42, re test2:#43"
        test_changeset13 = Changeset(None,1246,message,"test_person",time.time())
        self.check_ticket_comment(test_changeset13)

        tickets = self.obj1._parse_message(message)
        self.assertEqual(tickets.keys(),[])
        
        tickets = self.obj2._parse_message(message)
        self.assertEqual(tickets.keys(),[])

#------------------------------------------------------------------------------
# Utilities
    def build_comment(self,changeset):
        return """In [%d/%s]:
{{{
#!CommitTicketReference repository="%s" revision="%d"
%s
}}}""" % (changeset.rev, self.test_repo.name, self.test_repo.name, \
                                 changeset.rev, changeset.message)

    def check_ticket_comment(self,changeset):
        for obj in [self.obj1,self.obj2]:
            self.assertEqual(obj.make_ticket_comment(self.test_repo,changeset),
                             self.build_comment(changeset))

# Allow these tests to be run from the command line
if __name__ == '__main__':
    unittest.main()
