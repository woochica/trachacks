import unittest
from earnedValue.EVMacro import EVChartMacro

# This is the unit test for the getDateFromTicketDate() method in the EVMacro.py file.
# It tests that the date returned by the function matches the expected date.
# This unit test doesn't rely on the TestCaseInformation class at all.
class GetDateFromTicketTestCase(unittest.TestCase):
	
	def testValidDate(self):
		date = EVChartMacro.getDateFromTicket("2012-01-01", 1)
		assert date.day == 1, 'Incorrect day'
		assert date.month == 1, 'Incorrect month'
		assert date.year == 2012, 'Incorrect year'
		
	def testDateStringTooBig(self):
		try:
			date = EVChartMacro.getDateFromTicket("2012-01-001", 1)
		except:
			pass
		else:
			self.fail("Error expected")

	
	def testDateStringTooSmall(self):
		try:
			date = EVChartMacro.getDateFromTicket("2012-01-1", 1)
		except:
			pass
		else:
			self.fail("Error expected")
			
	def testInvalidFormat(self):
		try:
			date = EVChartMacro.getDateFromTicket("01-01-2012", 1)
		except:
			pass
		else:
			self.fail("Error expected")
			
	def testInvalidDay(self):
		try:
			date = EVChartMacro.getDateFromTicket("2012-01-32", 1)
		except:
			pass
		else:
			self.fail("Error expected")
			
	def testInvalidMonth(self):
		try:
			date = EVChartMacro.getDateFromTicket("2012-13-01", 1)
		except:
			pass
		else:
			self.fail("Error expected")
			
	def testInvalidYear(self):
		try:
			date = EVChartMacro.getDateFromTicket("20a2-01-01", 1)
		except:
			pass
		else:
			self.fail("Error expected")

	# Returns a test suite to be ran for this unit test.
	# When adding a new test method to this class, be sure to modify this method to include the method in the suite
	# EX: suite.addTest(GetDateFromTicketTestCase("methodName")
	@staticmethod
	def suite():
           suite = unittest.TestSuite()
           suite.addTest(GetDateFromTicketTestCase("testValidDate"))
           suite.addTest(GetDateFromTicketTestCase("testDateStringTooBig"))
           suite.addTest(GetDateFromTicketTestCase("testDateStringTooSmall"))
           suite.addTest(GetDateFromTicketTestCase("testInvalidFormat"))
           suite.addTest(GetDateFromTicketTestCase("testInvalidDay"))
           suite.addTest(GetDateFromTicketTestCase("testInvalidMonth"))
           suite.addTest(GetDateFromTicketTestCase("testInvalidYear"))
           return suite

	@staticmethod
	def runTestCases():
		runner = unittest.TextTestRunner()
		suite = GetDateFromTicketTestCase.suite()
		runner.run(suite)

if __name__ == "__main__":
	GetDateFromTicketTestCase.runTestCases()

