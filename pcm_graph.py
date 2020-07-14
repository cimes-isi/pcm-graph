#!/usr/bin/env python
import argparse
import csv
import re
import sys
import datetime

import numpy as np
import matplotlib.pyplot as plt

DAY_COL = 0
TIME_COL = 1


def _parse_csv(args):
    series = []
    series_labels = []

    with open(args.input, 'r') as f:
        reader = csv.reader(f, delimiter=',')

        # read and skip both header lines
        header = next(reader)
        subheader = next(reader)

        # create proper series labels by appending sub-header to current
        # main header
        current_head = header[0]
        for i, col in enumerate(subheader):
            if header[i]:
                current_head = header[i]

            # TODO: Why is it sometimes empty?
            # assert col != '', 'i = ' + str(i) + ', head = ' + current_head
            # if not col:
            #     col = 'UNKNOWN'
            series_labels.append(current_head + '::' + col)
            series.append([])

        # read values and write into series
        for line in reader:
            for i, val in enumerate(line):
                val = str(val).strip()

                if '%' in val:
                    val = float(val[:-1])

                try:
                    series[i].append(float(val))
                except ValueError:
                    series[i].append(val)

    return series_labels, series


def _create_time_series(series):
    x_series = []

    fake_day = datetime.date(2010, 1, 1)
    first_time = None

    for x, point in enumerate(series[TIME_COL]):
        # point is something like: 11:10:46.215
        h, m, s = [int(n) for n in point[:-4].split(':')]
        milli = int(point[-3:])
        u = datetime.time(h, m, s, milli * 1000)

        if not first_time:
            first_time = datetime.datetime.combine(fake_day, u)

        delta = (datetime.datetime.combine(fake_day, u) - first_time)
        x_series.append(delta.total_seconds())

    return x_series


def _is_filter_match(label):
    if label.endswith('Date') or label.endswith('Time'):
        return False
    label_t = label.split('::')[0]
    label_s = label.split('::')[1]
    if args.title:
        found = False
        for t in args.title:
            if args.regex:
                found = re.match(t, label_t)
            elif t == label_t:
                found = True
            if found:
                break
        if not found:
            return False
    if args.subtitle:
        for t in args.subtitle:
            if args.regex:
                if re.match(t, label_s):
                    return True
            elif t == label_s:
                return True
        return False
    return True


def _plot(args, series, series_labels, x_series):
    # plt.style.use(args.style) # FIXME

    # define color space
    color_space = 0
    for label in series_labels:
        if _is_filter_match(label):
            color_space += 1

    color_list = plt.cm.Set1(np.linspace(0, 1, color_space))

    color_n = 0
    for i, y_series in enumerate(series):
        label = series_labels[i]
        if not _is_filter_match(label):
            continue

        # sort in case PCM mixed up the order:
        y = [b for (x, b) in sorted(zip(x_series, y_series))]
        x = sorted(x_series)

        try:
            plt.plot(sorted(x_series), y, label=label, linewidth=2, linestyle='-',
                     color=color_list[color_n % color_space])
            color_n += 1
        except ValueError:
            # Sometimes we get blank columns?
            print('Error in column ' + str(i) + ': "' + label + '"')
            print(x)
            print(y)

    # plt.xticks(range(int(max(x_series) + 2)))

    if args.fig_title:
        plt.title(args.fig_title)
    elif args.title and args.subtitle:
        plt.title(str(args.title) + ' x ' + str(args.subtitle))
    elif args.title:
        plt.title(str(args.title))
    elif args.subtitle:
        plt.title('[\'.*\'] x ' + str(args.subtitle))

    plt.xlabel('Time (s)')
    # plt.ylabel('') # TODO

    plt.legend(prop={'size': 8})

    plt.xlim(right=plt.xlim()[1] * 1.3)

    plt.tight_layout()


def main(args):
    series_labels, series = _parse_csv(args)

    if not len(series_labels) or not len(series):
        print('No data found!')
        return

    # make sure that all data is from the same day
    if series[DAY_COL][0] != series[DAY_COL][-1]:
        print('We currently do not support measurements spanning more than a day. Sorry!')
        return

    # create correct x-series
    x_series = _create_time_series(series)

    # TODO: Average time series over time windows if too many entries?

    # print(x_series)
    _plot(args, series, series_labels, x_series)

    if args.output:
        plt.savefig(args.output)
    else:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='The PCM CSV file')
    # Title classes that are enumerated: Socket0, SKT0dataIn, SKT0dataIn (percent), SKT0trafficOut, SKT0trafficOut (percent), SKT0 Core C-State, SKT0 Package C-State
    # Title classes that are doubly enumerated: Core0 (Socket 0)
    parser.add_argument('-t', '--title', action='append',
                        help='Filter by title (e.g., System, System Core C-States, System Pack C-States, Socket0)')
    # Subtitle classes that are enumerated: UPI0, SKT0
    parser.add_argument('-s', '--subtitle', action='append',
                        help='Filter by subtitles (e.g., EXEC, IPC, FREQ, AFREQ)')
    parser.add_argument('-r', '--regex', action='store_true',
                        help='Treat -t and -s options as regular expressions')
    # parser.add_argument('-s', '--style', default='classic',
    #                     help='Define a custom matplotlib style to use, see `matplotlib.style`')
    parser.add_argument('-T', '--fig-title', help='Figure title')
    parser.add_argument('-o', '--output', help='Figure output file')
    args = parser.parse_args()

    main(args)
