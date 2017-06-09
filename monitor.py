#!/usr/bin/python3

import sys
import time
import argparse

from datetime import datetime


class Monitor():
    def __init__(self):
        self.logname = ''
        self.alert = 0
        self.alert_on = False
        self.alert_msg = (
                          'High traffic generated an alert - '
                          'hits = %d hits/min, triggered at %s'
                         )
        self.alert_msg_done = 'High traffic alert terminated at %s'
        self.cumul = False
        self.log = None
        self.lines_to_print = []
        self.top_section_hits = {}
        self.alert_history = []
        self.two_min_hits = []
        self.one_min_ave = 0.0
        self.stats = {'new_lines': 0, 'total_lines': 0, 'unique_ip': set()}

    def open_logfile(self, logfile):
        self.logname = logfile
        try:
            self.log = open(self.logname, 'r')
            # Go to EOF
            self.log.seek(0,2)
        except FileNotFoundError as e:
            print('Cannot open file : %s' % e)
            raise

    def close_logfile(self):
        self.log.close()

    def scan_log(self, cumul):
        self.cumul = cumul
        self.stats['new_lines'] = 0
        if not self.cumul:
            self.top_section_hits = {}

        for line in self.log.readlines():
            fields = line.split()
            # Get some useful statistics
            self.stats['unique_ip'].add(fields[0])
            self.stats['total_lines'] += 1
            self.stats['new_lines'] += 1

            # Get a section count
            # from a field formatted as :
            # " /x/y/x"
            # with a leading space
            # Only keep the URI and drop the remaining variables
            uri = fields[6].split('/')[2:]

            if uri:
                section = uri[0].split('?')[0]
                if section not in self.top_section_hits.keys():
                    self.top_section_hits[section] = 1
                else:
                    self.top_section_hits[section] += 1
        # Calculate hits/min average for a two minute
        # sliding window
        if len(self.two_min_hits) != 12:
            self.two_min_hits.append(self.stats['new_lines'])
        else:
            self.two_min_hits.pop(0)
            self.two_min_hits.append(self.stats['new_lines'])
            self.one_min_ave = sum(self.two_min_hits) / 2

    def check_alert(self, alert):
        self.alert = alert
        if self.one_min_ave > self.alert and not self.alert_on:
            now = datetime.now()
            self.alert_history += [self.alert_msg % (self.one_min_ave,
                                   now.strftime('%d/%b/%Y:%H:%M:%S'))]
            self.alert_on = True
        if self.one_min_ave <= self.alert and self.alert_on:
            now = datetime.now()
            self.alert_history += [self.alert_msg_done %
                                   now.strftime('%d/%b/%Y:%H:%M:%S')]
            self.alert_on = False

    def redraw_screen(self):
        # Start with a clean screen
        print('\033c', end='')

        # Print header
        print('Statistics for %s' % self.logname)
        print('Unique IP addresses : %d\t%d new entries of %d total entries' %
              (len(self.stats['unique_ip']), self.stats['new_lines'],
               self.stats['total_lines']))
        print('Last two minutes hits/min average : %d (alert level %d)' %
              (self.one_min_ave, self.alert))

        # Print top sections
        print('\n### Top sections hit ###')
        for section, hits in sorted(self.top_section_hits.items(),
                                    key=lambda x: x[1], reverse=True):
            print('%-40s%d' % (section, hits))

        # Print alert history
        print('\n### Alerts ###')
        for line in self.alert_history:
            print('%s' % line)


def main():

    monitor = Monitor()

    try:
        monitor.open_logfile(LogFile)
        while True:
            monitor.scan_log(Cumulative)
            monitor.check_alert(Alert)
            monitor.redraw_screen()
            time.sleep(Delay)
    except KeyboardInterrupt:
        print('Exiting on keyboard interrupt')
        monitor.close_logfile()
        sys.exit(0)
    except FileNotFoundError:
        sys.exit(1)


if __name__ == '__main__':

        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--filename', nargs=1, metavar='LOGFILE',
                            default='./mylogfile.log',
                            help='Path to logfile to monitor')
        parser.add_argument('-t', '--time', nargs=1, metavar='TIMEDELAY',
                            default=[10], type=int,
                            help='Time delay between updates')
        parser.add_argument('-a', '--alert', nargs=1, metavar='ALERT_LIMIT',
                            default=[200],
                            help='Hits/min alert threshold')
        parser.add_argument('-c', '--cumulative', action='store_true',
                            help='Print cumulative section hits')
        args = parser.parse_args()

        LogFile = args.filename
        Delay = args.time[0]
        Alert = float(args.alert[0])
        Cumulative = args.cumulative

        main()
