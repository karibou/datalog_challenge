#!/usr/bin/python3

import sys
import time
import argparse


def scan_log(logfile, lines):
    lines += ['scanning %s' % logfile]

def redraw_screen(lines):
    for line in lines:
        print('%s'% line)

def main():

    lines_to_print = []

    while True:
        time.sleep(Delay)
        scan_log(LogFile, lines_to_print)
        redraw_screen(lines_to_print)

if __name__ == '__main__':

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-f','--filename', nargs=1, metavar='LOGFILE',
                            default='./mylogfile.log',
                            help='Path to logfile to monitor')
        parser.add_argument('-t','--time', nargs=1, metavar='TIME DELAY',
                            default=10, type=int,
                            help='Time delay between updates')
        args = parser.parse_args()

        LogFile = args.filename[0]
        Delay = args.time[0]

        main()
    except KeyboardInterrupt:
        print('Exiting on keyboard interrupt')
        sys.exit(0)
