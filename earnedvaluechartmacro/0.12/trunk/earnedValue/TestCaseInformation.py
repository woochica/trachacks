
# This class holds all information used by the test cases.  The information is retrieved by the test cases through static method calls.
# This file was used so that all test case information could easily be changed in one location instead of having to edit each test case individually.
class TestCaseInformation:

	# The following methods are used by all test cases that use the database
	@staticmethod
	def getHost():
		return "localhost"
	@staticmethod
	def getUser():
		return "trac"
	@staticmethod
	def getPasswd():
		return "cart"
	@staticmethod
	def getDB():
		return "test"

	# The following method is used by the all tests involving real ticket data test
	@staticmethod
	def getTicketNumber():
		return 1

	# The following methods are all used by the GetEVDateTestCase.py test
	@staticmethod
	def getTicketEVDay():
		return 14
	@staticmethod
	def getTicketEVMonth():
		return 11
	@staticmethod
	def getTicketEVYear():
		return 2012

	# The following methods are all used by the GetPVDateTestCase.py test
	@staticmethod
	def getTicketPVDay():
		return 21
	@staticmethod
	def getTicketPVMonth():
		return 5
	@staticmethod
	def getTicketPVYear():
		return 2012

	# The following methods are all used by the GetStartDateTestCase.py test
	@staticmethod
	def getTicketStartDay():
		return 1
	@staticmethod
	def getTicketStartMonth():
		return 5
	@staticmethod
	def getTicketStartYear():
		return 2012

	# The following methods are all used by the GetValueTestCase.py test
	@staticmethod
	def getTicketEstimatedHours():
		return 1
