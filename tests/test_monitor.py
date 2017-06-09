import unittest
from datetime import datetime
from mock import patch, MagicMock
import monitor


class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.LogFile = './mylogfile.log'
        self.Delay = 20
        self.Alert = 20
        self.Cumulative = True

    def test_check_alert_on(self):
        t = datetime(1970, 10, 1, 12, 0, 0, 0)
        with patch('monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = t
            m = monitor.Monitor()
            m.one_min_ave = 30
            m.check_alert(self.Alert)
            alert_suffix = m.alert_history[0].partition(
                           'High traffic generated an alert - hits = ')[-1]
            self.assertEquals(alert_suffix,
                              '30 hits/min, triggered at 01/Oct/1970:12:00:00')

    def test_check_alert_off(self):
        t = datetime(1970, 10, 1, 12, 0, 0, 0)
        with patch('monitor.datetime') as mock_datetime:
            mock_datetime.now.return_value = t
            m = monitor.Monitor()
            m.one_min_ave = 10
            m.alert_on = True
            m.check_alert(self.Alert)
            self.assertEquals(m.alert_history[0], (
                              'High traffic alert terminated '
                              'at 01/Oct/1970:12:00:00'))

    def test_scan_log_cumulative(self):

        m = monitor.Monitor()
        m.log = MagicMock()
        m.log.readlines.return_value = [(
             '121.17.198.11 - - [09/Jun/2017:15:35:07 +0200] '
             '"DELETE /posts/posts/explore HTTP/1.0" 200 5038'
             '"http://cook.com/login/"')]
        m.scan_log(True)
        m.scan_log(True)
        self.assertEquals(m.top_section_hits['posts'], 2)

    def test_scan_log_non_cumulative(self):

        m = monitor.Monitor()
        m.log = MagicMock()
        m.log.readlines.return_value = [(
             '121.17.198.11 - - [09/Jun/2017:15:35:07 +0200] '
             '"DELETE /posts/posts/explore HTTP/1.0" 200 5038'
             '"http://cook.com/login/"')]
        m.scan_log(False)
        m.scan_log(False)
        self.assertEquals(m.top_section_hits['posts'], 1)
