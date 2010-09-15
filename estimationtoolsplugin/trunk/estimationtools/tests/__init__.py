
from unittest import TestSuite, makeSuite

def test_suite():
    suite = TestSuite()
    import estimationtools.tests.burndownchart
    suite.addTest(makeSuite(estimationtools.tests.burndownchart.BurndownChartTestCase))
    import estimationtools.tests.hoursremaining
    suite.addTest(makeSuite(estimationtools.tests.hoursremaining.HoursRemainingTestCase))
    import estimationtools.tests.workloadchart
    suite.addTest(makeSuite(estimationtools.tests.workloadchart.WorkloadChartTestCase))
    return suite
