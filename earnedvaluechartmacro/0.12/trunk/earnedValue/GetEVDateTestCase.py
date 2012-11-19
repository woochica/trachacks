import MySQLdb
import unittest
from earnedValue.EVMacro import EVChartMacro
from TestCaseInformation import TestCaseInformation

# This is the unit test for the getEVDate() method in the EVMacro.py file.
# It tests that the date returned by the function matches the expected date.
# Information used for this test resides in TestCaseInformation.getTicketEV* methods as well as the database information.
class GetEVDateTestCase(unittest.TestCase):
	def setUp(self):
		self.db = MySQLdb.connect(host=TestCaseInformation.getHost(), user=TestCaseInformation.getUser(), passwd=TestCaseInformation.getPasswd(),
db=TestCaseInformation.getDB())

	def testValidDate(self):
		date = EVChartMacro.getEVDate(self.db.cursor(), TestCaseInformation.getTicketNumber())
		assert date.day == TestCaseInformation.getTicketEVDay(), 'Incorrect day'
		assert date.month == TestCaseInformation.getTicketEVMonth(), 'Incorrect month'
		assert date.year == TestCaseInformation.getTicketEVYear(), 'Incorrect year'


	def testNoDate(self):
		date = EVChartMacro.getEVDate(self.db.cursor(), -1)
		assert date == NONE, 'Expected None type'

	# Returns a test suite to be ran for this unit test.
	# When adding a new test method to this class, be sure to modify this method to include the method in the suite
	# EX: suite.addTest(GetEVDateTestCase("methodName")
	@staticmethod
	def suite():
           suite = unittest.TestSuite()
           suite.addTest(GetEVDateTestCase("testValidDate"))
	   suite.addTest(GetEVDateTestCase("testNoDate"))
           return suite

	@staticmethod
	def runTestCases():
		runner = unittest.TextTestRunner()
		suite = GetEVDateTestCase.suite()
		runner.run(suite)

if __name__ == "__main__":
	GetEVDateTestCase.runTestCases()
