from GetDateFromTicketTestCase import GetDateFromTicketTestCase
from GetValueTestCase import GetValueTestCase
from GetStartDateTestCase import GetStartDateTestCase
from GetPVDateTestCase import GetPVDateTestCase
from GetEVDateTestCase import GetEVDateTestCase


# This method allows for all of the tests to be ran at the same time.  It calls the runTestCases() method on each test case.
# When adding a new PyUnit test module, add a new section to the runTests() method to include your test case.
# Information used by the test cases can be viewed and modified in the TestCaseInformation.py file.
# Major information stored there includes database connection info and expected values for most modules.
# EX: 
# print "Running 'TEST_CASE_NAME' Test Cases"
# TEST_CASE_CLASS.runTestCases()
# print "Finished"
def runTests():
	print "Running 'GetDateFromTicket' Test Cases"
	GetDateFromTicketTestCase.runTestCases()
	print "Finished"

	print "Running 'GetValue' Test Cases"
	GetValueTestCase.runTestCases()
	print "Finished"

	print "Running 'GetStartDate' Test Cases"
	GetStartDateTestCase.runTestCases()
	print "Finished"

	print "Running 'GetPVDate' Test Cases"
	GetPVDateTestCase.runTestCases()
	print "Finished"

	print "Running 'GetEVDate' Test Cases"
	GetEVDateTestCase.runTestCases()
	print "Finished"

if __name__ == "__main__":
	runTests()


