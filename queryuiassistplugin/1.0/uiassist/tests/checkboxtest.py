from selenium import selenium
import time
import unittest


class Test(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.selenium = selenium("localhost", 4444, "*chrome", "http://localhost:8080/1.0/")
        self.selenium.start()

    def test_double_click_field_from_uri(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        sel.double_click("label_0_status")
        self.failUnless(not sel.is_checked("_0_status_accepted"))
        self.failUnless(not sel.is_checked("_0_status_assigned"))
        self.failUnless(sel.is_checked("_0_status_closed"))
        self.failUnless(not sel.is_checked("_0_status_new"))
        self.failUnless(not sel.is_checked("_0_status_reopened"))

    def test_double_click_field_added_by_adder(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        time.sleep(2)
        sel.select("add_filter_0", "Vote")
        sel.double_click("label_0_vote")
        self.failUnless(sel.is_checked("0_vote_a"))
        self.failUnless(sel.is_checked("0_vote_b"))
        self.failUnless(sel.is_checked("0_vote_c"))
        self.failUnless(sel.is_checked("0_vote_d"))
        # regression
        sel.double_click("label_0_status")
        self.failUnless(not sel.is_checked("_0_status_accepted"))
        self.failUnless(not sel.is_checked("_0_status_assigned"))
        self.failUnless(sel.is_checked("_0_status_closed"))
        self.failUnless(not sel.is_checked("_0_status_new"))
        self.failUnless(not sel.is_checked("_0_status_reopened"))

    def test_double_click_field_added_by_adder_repeatly(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        time.sleep(2)
        sel.select("add_filter_0", "Vote")
        sel.double_click("label_0_vote")
        sel.uncheck("0_vote_c")
        sel.double_click("label_0_vote")
        self.failUnless(not sel.is_checked("0_vote_a"))
        self.failUnless(not sel.is_checked("0_vote_b"))
        self.failUnless(sel.is_checked("0_vote_c"))
        self.failUnless(not sel.is_checked("0_vote_d"))

    def test_double_click_on_checkbox(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        sel.double_click("_0_status_accepted")
        self.failUnless(sel.is_checked("_0_status_accepted"))
        self.failUnless(not sel.is_checked("_0_status_assigned"))
        self.failUnless(not sel.is_checked("_0_status_closed"))
        self.failUnless(not sel.is_checked("_0_status_new"))
        self.failUnless(not sel.is_checked("_0_status_reopened"))

    def test_double_click_on_checkbox_label(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        sel.double_click("//label[@for='_0_status_accepted']")
        self.failUnless(sel.is_checked("_0_status_accepted"))
        self.failUnless(not sel.is_checked("_0_status_assigned"))
        self.failUnless(not sel.is_checked("_0_status_closed"))
        self.failUnless(not sel.is_checked("_0_status_new"))
        self.failUnless(not sel.is_checked("_0_status_reopened"))

    def test_double_click_on_checkbox_label_added_by_adder(self):
        sel = self.selenium
        sel.open("query?status=!closed")
        time.sleep(2)
        sel.select("add_filter_0", "Vote")
        sel.double_click("//label[@for='0_vote_a']")
        sel.double_click("//label[@for='0_vote_c']")
        self.failUnless(not sel.is_checked("0_vote_a"))
        self.failUnless(not sel.is_checked("0_vote_b"))
        self.failUnless(sel.is_checked("0_vote_c"))
        self.failUnless(not sel.is_checked("0_vote_d"))

    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)
