import unittest
import sys
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

    def test_scan_log_with_average(self):

        m = monitor.Monitor()
        m.log = MagicMock()
        m.log.readlines.return_value = [(
             '121.17.198.11 - - [09/Jun/2017:15:35:07 +0200] '
             '"DELETE /posts/posts/explore HTTP/1.0" 200 5038'
             '"http://cook.com/login/"')]
        for _ in range(13):
            m.scan_log(False)
        self.assertEquals(len(m.two_min_hits), 12)
        self.assertEquals(m.one_min_ave, 6)

    def test_redraw_screen_top_section(self):

        m = monitor.Monitor()
        m.logname = './mylogfile.log'
        m.alert_history
        m.redraw_screen()
        output = sys.stdout.getvalue().strip()
        self.assertEquals(output, '''\x1bcStatistics for ./mylogfile.log
Unique IP addresses : 0	0 new entries of 0 total entries
Last two minutes hits/min average : 0 (alert level 0)

### Top sections hit ###

### Alerts ###''')

    def test_redraw_screen_alert(self):

        m = monitor.Monitor()
        m.logname = './mylogfile.log'
        m.alert_history = ['First alert', 'Second alert']
        m.redraw_screen()
        output = sys.stdout.getvalue().strip()
        self.assertEquals(output, '''\x1bcStatistics for ./mylogfile.log
Unique IP addresses : 0	0 new entries of 0 total entries
Last two minutes hits/min average : 0 (alert level 0)

### Top sections hit ###

### Alerts ###
First alert
Second alert''')

    def test_open_logfile_existing(self):

        m = monitor.Monitor()
        fake_file = MagicMock()
        with patch('builtins.open', return_value=fake_file):
            m.open_logfile('./mylogfile.log')

    def test_open_logfile_do_not_exist(self):

        m = monitor.Monitor()
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = FileNotFoundError
            with self.assertRaises(FileNotFoundError):
                m.open_logfile('./mylogfile.log')

    @patch('monitor.Monitor.open_logfile')
    @patch('monitor.Monitor.close_logfile')
    @patch('monitor.Monitor.scan_log')
    @patch('monitor.Monitor.check_alert')
    @patch('monitor.Monitor.redraw_screen')
    def test_main_kbd_interrupt(self, m_open, m_close, m_scan, m_alert,
                                m_redraw):

        with patch('monitor.time.sleep', side_effect=KeyboardInterrupt):
            with patch('monitor.sys.exit'):
                monitor.LogFile = './mylogfile.log'
                monitor.Cumulative = False
                monitor.Alert = 20
                monitor.Delay = 10
                monitor.main()
                output = sys.stdout.getvalue().strip()
                self.assertEquals(output, 'Exiting on keyboard interrupt')

    def test_main_file_not_found(self):

        with patch('builtins.open') as mock_open:
            mock_open.side_effect = FileNotFoundError
            with patch('monitor.sys.exit'):
                monitor.LogFile = './mylogfile.log'
                monitor.main()
                output = sys.stdout.getvalue().strip()
                self.assertEquals(output, 'Cannot open file :')
