import MySQLdb
import unittest
from earnedValue.EVMacro import EVChartMacro
from TestCaseInformation import TestCaseInformation

# This is the unit test for the getStartDate() method in the EVMacro.py file.
# It tests that the date returned by the function matches the expected date.
# Information used for this test resides in TestCaseInformation.getTicketStart* methods as well as the database information.
class GetStartDateTestCase(unittest.TestCase):
	# Sets up the database connection
	def setUp(self):
		self.db = MySQLdb.connect(host=TestCaseInformation.getHost(), user=TestCaseInformation.getUser(), passwd=TestCaseInformation.getPasswd(),
db=TestCaseInformation.getDB())

	def testValidDate(self):
		date = EVChartMacro.getStartDate(self.db.cursor(), TestCaseInformation.getTicketNumber())
		assert date.day == TestCaseInformation.getTicketStartDay(), 'Incorrect day'
		assert date.month == TestCaseInformation.getTicketStartMonth(), 'Incorrect month'
		assert date.year == TestCaseInformation.getTicketStartYear(), 'Incorrect year'

	def testNoDate(self):
		date = EVChartMacro.getStartDate(self.db.cursor(), -1)
		assert date == None, 'Expected None type'

	# Returns a test suite to be ran for this unit test.
	# When adding a new test method to this class, be sure to modify this method to include the method in the suite
	# EX: suite.addTest(GetStartDateTestCase("methodName")
	@staticmethod
	def suite():
           suite = unittest.TestSuite()
           suite.addTest(GetStartDateTestCase("testValidDate"))
	   suite.addTest(GetStartDateTestCase("testNoDate"))
           return suite

	@staticmethod
	def runTestCases():
		runner = unittest.TextTestRunner()
		suite = GetStartDateTestCase.suite()
		runner.run(suite)

if __name__ == "__main__":
	GetStartDateTestCase.runTestCases()
