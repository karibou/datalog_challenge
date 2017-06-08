#!/usr/bin/python3

import sys
import time
import argparse


class Monitor():
    def __init__(self, logfile):
        self.log = logfile
        self.lines_to_print = []

    def scan_log(self):
        self.lines_to_print += ['scanning %s' % self.log]

    def redraw_screen(self):
        for line in self.lines_to_print:
            print('%s' % line)


def main():

    monitor = Monitor(LogFile)

    while True:
        time.sleep(Delay)
        monitor.scan_log()
        monitor.redraw_screen()


if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--filename', nargs=1, metavar='LOGFILE',
                            default='./mylogfile.log',
                            help='Path to logfile to monitor')
        parser.add_argument('-t', '--time', nargs=1, metavar='TIMEDELAY',
                            default=10, type=int,
                            help='Time delay between updates')
        args = parser.parse_args()

        LogFile = args.filename
        Delay = args.time[0]

        main()
    except KeyboardInterrupt:
        print('Exiting on keyboard interrupt')
        sys.exit(0)
