import MySQLdb
import unittest
from earnedValue.EVMacro import EVChartMacro
from TestCaseInformation import TestCaseInformation

# This is the unit test for the getPVDate() method in the EVMacro.py file.
# It tests that the date returned by the function matches the expected date.
# Information used for this test resides in TestCaseInformation.getTicketPV* methods as well as the database information.

class GetPVDateTestCase(unittest.TestCase):
	def setUp(self):
		self.db = MySQLdb.connect(host=TestCaseInformation.getHost(), user=TestCaseInformation.getUser(), passwd=TestCaseInformation.getPasswd(),
db=TestCaseInformation.getDB())

	def testValidDate(self):
		date = EVChartMacro.getPVDate(self.db.cursor(), TestCaseInformation.getTicketNumber())
		assert date.day == TestCaseInformation.getTicketPVDay(), 'Incorrect day'
		assert date.month == TestCaseInformation.getTicketPVMonth(), 'Incorrect month'
		assert date.year == TestCaseInformation.getTicketPVYear(), 'Incorrect year'

	def testNoDate(self):
		date = EVChartMacro.getPVDate(self.db.cursor(), -1)
		assert date == None, 'Expected None type'

	# Returns a test suite to be ran for this unit test.
	# When adding a new test method to this class, be sure to modify this method to include the method in the suite
	# EX: suite.addTest(GetPVDateTestCase("methodName")
	@staticmethod
	def suite():
           suite = unittest.TestSuite()
           suite.addTest(GetPVDateTestCase("testValidDate"))
	   suite.addTest(GetPVDateTestCase("testNoDate"))
           return suite

	@staticmethod
	def runTestCases():
		runner = unittest.TextTestRunner()
		suite = GetPVDateTestCase.suite()
		runner.run(suite)

if __name__ == "__main__":
	GetPVDateTestCase.runTestCases()
