from trac.wiki.macros import WikiMacroBase
#from trac.util.html import Markup
from trac.wiki import Formatter
from genshi.core import Markup
from trac.env import Environment
from trac.db import with_transaction
from datetime import *
from GChartWrapper import *
import sys
import traceback

import unittest




class EVChartMacro(WikiMacroBase):
	"""Create a chart using the Google Chart API.

	Examples:
	{{{
	[[EVChart(Cycle 8)]]
	}}}
	"""

	# Converts a given string in form YYYY-MM-DD to a date object
	@staticmethod
	def getDateFromTicket(inputDate, ticket):
		if len(inputDate) != 10:
			raise Exception("Error: Date passed from Ticket #%s does not match YYYY-MM-DD syntax.  (Date passed was %s.)" % (ticket, inputDate))
		try:
			year = inputDate[:4]
			month = inputDate[5:7]
			day = inputDate[8:10]
			retDate = date(int(year), int(month), int(day))
		except:
			raise Exception("Error: Date passed from Ticket #%s is not a valid date.  (Date passed was %s.)" % (ticket, inputDate))
		return retDate
		
	
	# Returns the date the ticket was closed.
	# Returns NONE if the ticket has never been closed.
	# @param ticket - ticket id
	@staticmethod
	def getEVDate(cursor, ticket):

		# Pull the latest change to the status where the ids match
		sql = """SELECT `time`, `newvalue` FROM `ticket_change` 
			WHERE `field` = "status" 
			AND `ticket` = %s
			ORDER BY `time` DESC
			LIMIT 1""" % (ticket)


		#db = self.env.get_db_cnx()
		#cursor = db.cursor()
		cursor.execute(sql)

		results = []

		for row in cursor:
			rowData = []
			for col in row:
				rowData.append(col)
			results.append(rowData)

		# If the status has never been changed, return None
		if len(results) != 1:
			return None
		
		# Grab the only tuple and put it in result
		result = results[0]

		# If the ticket isn't closed, return None
		if result[1] != u'closed':
			return None		

		# Time returned is stored in Unix Time, so convert it to a date object and return
		return date.fromtimestamp( float( result[0]/1000000.0 ) )
	
	# Returns the planned finish date of the ticket
	# @param ticket - ticket id
	@staticmethod
	def getPVDate(cursor, ticket):
		# Pull the estimated date from ticket_custom where the ids match
		sql = """SELECT `value` FROM `ticket_custom`
			WHERE `ticket` = %s
			AND `name` = "end"
			LIMIT 1""" % (ticket)
			
		#db = self.env.get_db_cnx()
        	#cursor = db.cursor()
		cursor.execute(sql)
		
		results = []
		
		for row in cursor:
			rowData = []
			for col in row:
				rowData.append(col)
			results.append(rowData)
		
		# If the date has never been set, return None
		if len(results) != 1:
			return None


		# Grab the only tuple and put it in result
		result = results[0]


		# Convert the timestamp to a date object
		return EVChartMacro.getDateFromTicket(result[0], ticket)
		

	# Returns the planned start date of the ticket
	# @param ticket - ticket id
	@staticmethod
	def getStartDate(cursor, ticket):
		# Pull the estimated date from ticket_custom where the ids match
		sql = """SELECT `value` FROM `ticket_custom`
			WHERE `ticket` = %s
			AND `name` = "start"
			LIMIT 1""" % (ticket)
			
		#db = self.env.get_db_cnx()
        	#cursor = db.cursor()
		cursor.execute(sql)
		
		results = []
		
		for row in cursor:
			rowData = []
			for col in row:
				rowData.append(col)
			results.append(rowData)
		
		# If the date was never set, return NONE
		if len(results) != 1:
			return None

		# Grab the only tuple and put it in result
		result = results[0]

		# Convert the timestamp to a date object
		return EVChartMacro.getDateFromTicket(result[0], ticket)

	# Returns the estimated hours (earned value) for the ticket
	# @param ticket - Ticket id
	@staticmethod
	def getValue(cursor, ticket):
		# Pull the value from ticket_custom where the ids match
		sql = """SELECT `value` FROM `ticket_custom` 
			WHERE `ticket` = %s
			AND `name` = "estimatedhours"
			LIMIT 1""" % (ticket)
			
		#db = self.env.get_db_cnx()
        	#cursor = db.cursor()
		cursor.execute(sql)
		
		
		results = []
		for row in cursor:
			results.append( float(row[0]) )

		# If no estimate was made, return 0
		if len(results) == 0:
			return 0
		
		# Grab what should be the only value and put it in result
		result = results[0]
		return result
		
		
		
	
	# Makes a graph of Week vs Value and plots a line for CEV and CPV.
	# The x axis is labeled in week number.  The y axis is labeled as % value.
	# @param ticketIds - List of ticket ids to pull value and dates from
	# @param startDate - Python date object representing the date to start from
	# @param endDate - Python date object representing the ending date
	def makeGraph(self, ticketIds, startDate, endDate):
		# find the span of the dates
		span = endDate - startDate
		
		#If and end date wasnt found or the day span is negative, return 0
		if startDate is None or endDate is None or span is None:
			return 0
		

		# These arrays are of length span+1.  Each index represents a day between
		# startDate and endDate inclusive.
		dataPV = [0] * (span.days+1)
		dataEV = [0] * (span.days+1)
		
		# Stores the PV or EV for any given day in the array
		for id in ticketIds:

			try:
				# Bool representing if the ticket has EV
				hasEV = 0
				# Gets the date to add earned value to
				evIndex = EVChartMacro.getEVDate(self.env.get_db_cnx().cursor(), id)

				# If the ticket has been closed, set hasEV to true
				if not(evIndex is None):
					hasEV = 1
				else:
				# Otherwise give evIndex a value so that calculations aren't messed up
					evIndex = startDate

				# Gets the date to add planned value to
				pvIndex = EVChartMacro.getPVDate(self.env.get_db_cnx().cursor(), id)
				if (pvIndex is None):
					pvIndex = endDate

				# Changes the variables into datetime objects with the time between the startDate
				# of the milestone and the EV or PV dates.
				evIndex = evIndex - startDate
				pvIndex = pvIndex - startDate

				# Value for a ticket
				value = EVChartMacro.getValue(self.env.get_db_cnx().cursor(), id)
				
				# Range checking
				if int(pvIndex.days) >= len(dataPV):
					#if the end date is out of bounds, default it to the end of the milestone
					pvIndex = endDate - startDate			
				if int(pvIndex.days) < 0:
					raise ValueError('Error: The planned end date for Ticket #%s is before the start of the milestone (%s)' % (id, startDate))
	
				# Add to the value for that day
				dataPV[int(pvIndex.days)] = dataPV[int(pvIndex.days)] + value
				if hasEV:
					if int(evIndex.days) < len(dataEV):
						dataEV[int(evIndex.days)] = dataEV[int(evIndex.days)] + value
			except Exception as e:
				raise e
				raise Exception('Error: Unexpected error with Ticket #%s.  Please check that the ticket has start and end dates in the form YYYY-MM-DD.' % (id))
		
		"""
		In order to plot earned value by days instead of by weeks, you would use the dataPV and dataEV arrays for plotting in place of the CEV and CPV arrays created below.
		The x-axis would need to be changed to be the length of the span of days instead of the number of weeks.
		To avoid cluttering up the x-axis label, you can insert 'NONE' values into the axis to display a blank label and only show an actual date every 7 days or so.
		An example of the 'NONE' label can be seen in the first element of the y-axis label below.

		"""


		#Determine the number of weeks in the span
		weeks = (span.days+1) / 7
		if (span.days+1)%7 > 0:
			weeks = weeks + 1

		# Initialize cumulative value lists
		CPV = [0] * weeks
		CEV = [0] * weeks

		# Convert from the days to the weeks
		for week in range(0, weeks):
			
			# Dynamically adds the previous weeks to the current week
			if week != 0:
				CPV[week] = float(CPV[ week - 1 ])
				CEV[week] = float(CEV[ week - 1 ])
			
			# Add new value to the week
			for day in range(0, 7):

				# Calculate the index into the span
				index = day + week*7

				if week == 0:
					index = day
				
				# Exit if the index goes over the span
				# Possible if there is less than 7 days in the final week
				if index >= int(span.days+1):
					break
				
				# Add the value
				CPV[week] = float(CPV[week] + dataPV[index])
				CEV[week] = float(CEV[week] + dataEV[index])
				
		# determine the maximum amount of PV
		maxPV = float(CPV[ len(CPV) - 1 ])
		if maxPV == 0:
			maxPV = 1.0
		
		# Turn the values into percentages
		for x in range(0, weeks):
			CPV[x] = (CPV[x]/maxPV) * 100.0
			CEV[x] = (CEV[x]/maxPV) * 100.0
		
		CPV.insert(0, 0)
		CEV.insert(0, 0)

		# create the lined chart with the data
		chart = Line([CPV,CEV])

		# set the size of the chart
		chart.size(600,300)

		# set the color for each line
		chart.color('red','blue')
		
		# create a legend with the CPV and CEV
		chart.legend('CPV','CEV')

		# create axes for the chart
		chart.axes('yx')

		# Generate the x axis label
		axesLabel = []
		for x in range (0, weeks):
			tempdate = datetime(startDate.year, startDate.month, startDate.day) + timedelta(days=(7*x))
			axesLabel.append("%s/%s" % (tempdate.month, tempdate.day))
		axesLabel.append("%s/%s" % (endDate.month, endDate.day))
		# set the axes labels
		chart.axes.label(0,None,'10%','20%','30%','40%','50%','60%','70%','80%','90%','100%')
		chart.axes.label(1, *axesLabel)

		return chart
		

	# This is what gets called whenever the macro is used in the wiki
	# It determines the start and end dates for the milestone and generates the EV chart
	# It gets called using [[EVMacro(Milestone)]] on any trac wiki page
	def expand_macro(self, formatter, name, text, args):
		# Gets the milestone from the params
		milestone = text

		# Open DB connection
		db = self.env.get_db_cnx()
		cursor = db.cursor()

		# SQL to determine if the milestone exists
		query = """SELECT * FROM milestone
			WHERE name = "%s"
			""" % (milestone)

		if cursor.execute(query) == 0:
			raise Exception('The milestone "%s" doesn\'t exist in the database' % (milestone) )


		# SQL to select all tickets for the milestone
		query = """SELECT `id` FROM `ticket`
			WHERE `milestone` = "%s"
			""" % (milestone)

		# Executes statement
		cursor.execute(query)

		# holds all ticket IDs as they are discovered
		dataset = []
		# Tracks the first created ticket, used for determining start date
		startDate = 0
		

		for row in cursor:
			
			#temp ticket
			curTicket = int(row[0])
			try:
				#temp time
				curTime = EVChartMacro.getStartDate(self.env.get_db_cnx().cursor(), curTicket)

				if curTime is None:
					curTime = startDate

				#add ticket id
				dataset.append(curTicket)

				#determine earliest ticket
				if startDate == 0:
					startDate = curTime
				else :
					if curTime < startDate:
						startDate = curTime
			except:
				raise Exception('Error: Unexpected error with Ticket #%s.  Please check that the ticket has start and end dates in the form YYYY-MM-DD.' % (curTicket))
		if startDate == 0:
			raise Exception('Error: At least one ticket must have a start date.')		

		if len(dataset) == 0:
			raise Exception('Error: Milestone must contain at least one ticket')

		# SQL to determine end date of the milestone
		query = """SELECT due FROM milestone
			WHERE name = "%s"
			""" % (milestone)

		cursor.execute(query)
		
		# End date for the milestone in Unix time (microseconds)
		endTime = 0

		for row in cursor:
			endTime = float(row[0])
		
		if endTime == 0:
			raise Exception('Error: Milestone must have an end date')

		# convert to seconds
		endTime = float(endTime / 1000000.0)
		endDate = date.fromtimestamp( float(endTime) )

		#Makes the graph
		chart = self.makeGraph(dataset, startDate, endDate)
		#Renders the graph and gives it back to the wiki
		return chart.img()


