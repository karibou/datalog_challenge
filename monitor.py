#!/usr/bin/python3

import sys
import time
import argparse
import re

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
        self.ip_regex = re.compile(r'^.* - -')
        self.uri_regex = re.compile(r'\"*\"')
        self.section_regex = re.compile(r'\s+')

    def open_logfile(self, logfile):
        self.logname = logfile
        try:
            self.log = open(self.logname, 'r')
            # Go to EOF
            self.log.seek(0, 2)
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
            # Get some useful statistics
            ip_block = self.ip_regex.search(line)
            if ip_block:
                ip = ip_block.group().strip(' - -')
                self.stats['unique_ip'].add(ip)
            self.stats['total_lines'] += 1
            self.stats['new_lines'] += 1

            # Get the URI
            # Format is "CMD /section/subsections HTTP/{vers}'
            # Drop CMD and split rest in list
            uri = self.uri_regex.split(line)
            if len(uri) >= 2:
                uri_fields = self.section_regex.split(uri[1])
                if len(uri_fields) >= 2:
                    section = uri_fields[1].split('/')

                    if len(section) >= 3:
                        # Drop the trailing variables if they exist
                        if '?' in section[2]:
                            section[2] = section[2].split('?')[0]

                        if section[2] not in self.top_section_hits.keys():
                            self.top_section_hits[section[2]] = 1
                        else:
                            self.top_section_hits[section[2]] += 1
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
        parser.add_argument('-f', '--filename', metavar='LOGFILE',
                            default='./mylogfile.log', type=str,
                            help='Path to logfile to monitor')
        parser.add_argument('-t', '--time', metavar='TIMEDELAY',
                            default=10, type=int,
                            help='Time delay between updates')
        parser.add_argument('-a', '--alert', metavar='ALERT_LIMIT',
                            type=float, default=100.0,
                            help='Hits/min alert threshold')
        parser.add_argument('-c', '--cumulative', action='store_true',
                            help='Print cumulative section hits')
        args = parser.parse_args()

        LogFile = args.filename
        Delay = args.time
        Alert = args.alert
        Cumulative = args.cumulative

        main()
