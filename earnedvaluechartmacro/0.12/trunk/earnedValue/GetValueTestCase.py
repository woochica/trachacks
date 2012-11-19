import MySQLdb
import unittest
from earnedValue.EVMacro import EVChartMacro
from TestCaseInformation import TestCaseInformation

# This is the unit test for the getValue() method in the EVMacro.py file.
# It tests that the date returned by the function matches the expected date.
# Information used for this test resides in TestCaseInformation.getTicketEstimatedHours() method as well as the database information.
class GetValueTestCase(unittest.TestCase):
	def setUp(self):
		self.db = MySQLdb.connect(host=TestCaseInformation.getHost(), user=TestCaseInformation.getUser(), passwd=TestCaseInformation.getPasswd(),
db=TestCaseInformation.getDB())

	def testValidValue(self):
		value = EVChartMacro.getValue(self.db.cursor(), TestCaseInformation.getTicketNumber())
		assert value == TestCaseInformation.getTicketEstimatedHours(), 'Invalid value'

	def testNoValue(self):
		value = EVChartMacro.getValue(self.db.cursor(), -1)
		assert value == 0, 'Invalid value'

	# Returns a test suite to be ran for this unit test.
	# When adding a new test method to this class, be sure to modify this method to include the method in the suite
	# EX: suite.addTest(GetValueTestCase("methodName")
	@staticmethod
	def suite():
           suite = unittest.TestSuite()
           suite.addTest(GetValueTestCase("testValidValue"))
	   suite.addTest(GetValueTestCase("testNoValue"))
           return suite

	@staticmethod
	def runTestCases():
		runner = unittest.TextTestRunner()
		suite = GetValueTestCase.suite()
		runner.run(suite)

if __name__ == "__main__":
	GetValueTestCase.runTestCases()
