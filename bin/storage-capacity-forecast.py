#!/usr/bin/env python
# perform some forecasting based on storage usage data
import sys
import argparse
import time
import datetime

from influxdb.influxdb08 import InfluxDBClient
from pyVsphereInflux import InfluxResult08

influx_dsn_default = "influxdb://root:root@localhost:8086/database"
data_spec = {
              '/xioprop..*/': { 'used':     'UD-SSD-Space-In-Use',
                                'capacity': 'UD-SSD-Space',
                                'bytes_factor': 1 },
              '/vnxprop..*/': { 'used':     'Consumed_Capacity__GBs_',
                                'capacity': 'User_Capacity__GBs_',
                                'bytes_factor': 2**30 },
            }

def basic_linear_regression(x, y):
    """Compute a linear regression given arrays of points X and Y
        http://jmduke.com/posts/basic-linear-regressions-in-python/"""
    # Basic computations to save a little time.
    length = len(x)
    sum_x = sum(x)
    sum_y = sum(y)

    # sum(x^2), and sum(xy) respectively.
    sum_x_squared = sum(map(lambda a: a * a, x))
    sum_of_products = sum([x[i] * y[i] for i in range(length)])

    # Magic formulae!  
    a = (sum_of_products - (sum_x * sum_y) / length) / (sum_x_squared - ((sum_x ** 2) / length))
    b = (sum_y - a * sum_x) / length
    return a, b

def get_raw_data(args):
    # find raw points in database
    client = InfluxDBClient.from_DSN(args.influx_dsn)
    
    # get series to query
    check_series = {}
    for list_spec in data_spec:
        series = InfluxResult08.query(client, "list series %s" % list_spec)
        check_series[list_spec] = []
        for s in series:
            check_series[list_spec].extend(s.fields.values())

    # query the series and record the results according to the data spec 
    # and command line arguments
    data_points = {}

    for list_spec in check_series:
        for series in check_series[list_spec]:
            query = """SELECT 
                        mean("%s") AS "used", 
                        mean("%s") AS "capacity"
                       FROM %s 
                       WHERE time > now() - %sd
                       GROUP BY time(%sd) ORDER ASC""" % \
                       (data_spec[list_spec]['used'], 
                        data_spec[list_spec]['capacity'],
                        series, args.range, args.interval)

            res = InfluxResult08.query(client, query)
            for ts in res:
                ts.tags['bytes_factor'] = data_spec[list_spec]['bytes_factor']
            data_points[series] = res

    return data_points

def main():
    # take some input 
    parser = argparse.ArgumentParser(description="storage capacity forecasting based on influxdb data")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--range', default=120, type=int,
                        help="Range of history to search in days (default: 120)")
    parser.add_argument('--interval', default=1, type=int,
                        help="Summarization interval for data points in days (default: 1)")
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    data_points = get_raw_data(args)

    # compute regressions for the purposes of forecasting
    regressions = {}
    for series in data_points:
        latest_ts = data_points[series][-1]
        # get latest capacity normalized to bytes
        bytes_factor = latest_ts.tags['bytes_factor']
        x = [ts.timestamp for ts in data_points[series]]
        y = [ts.fields['used'] * bytes_factor for ts in data_points[series]]
        m, b = basic_linear_regression(x, y)
        regressions[series] = (m, b)

    # come up with some useful results (forecasts)
    # y = m * x + b
    # x = time
    # y = used
    results = {}
    for series in regressions:
        latest_ts = data_points[series][-1]
        # get latest capacity normalized to bytes
        bytes_factor = latest_ts.tags['bytes_factor']
        latest_used = latest_ts.fields['used'] * bytes_factor
        latest_cap = latest_ts.fields['capacity'] * bytes_factor
        # what's the amount remaining?
        latest_remaining = latest_cap - latest_used
        # what's the latest percentage used?
        percent_used = latest_used / latest_cap * 100
        # when will used intercept capacity?
        # set y = capacity, solve for x
        # (y - b) / m
        full_ts = (latest_cap - regressions[series][1]) / regressions[series][0]
        secs_until_full = full_ts - time.time()
        # when will used hit 90% capacity?
        # set y = capacity * 0.9, solve for x
        # (y - b) / m
        ninety_full_ts = (latest_cap * 0.9 - regressions[series][1]) / \
                      regressions[series][0]
        secs_until_ninety_full = ninety_full_ts - time.time()

        # stuff the results into a dict
        results[series] = {}
        results[series]['latest_used'] = latest_used
        results[series]['latest_capacity'] = latest_cap
        results[series]['latest_remaining'] = latest_remaining
        results[series]['percent_used'] = percent_used
        results[series]['full_ts'] = full_ts
        results[series]['secs_until_full'] = secs_until_full
        results[series]['ninety_full_ts'] = ninety_full_ts
        results[series]['secs_until_ninety_full'] = secs_until_ninety_full


    if args.debug:
        print "Raw data points:"
        for s in data_points:
            print "Series:", s
            print "Points:", data_points[s]
            print
        print "Regressions:"
        for s in regressions:
            print "Series:", s
            print "Regression: y = %.3f * x + %.3f" % regressions[s]
            print
        print "Statistics:"
        for s in results:
            print "Series:", s
            print "Results:", results[s]
            print

    # print results
    print "Array or Pool, Used, Remaining Capacity, Percent Full, Days Until 90% Full"
    for series in results:
        r_val = results[series]

        try:
            td = datetime.timedelta(seconds=r_val['secs_until_ninety_full'])
            remaining_time = "%d days" % td.days
        except OverflowError:
            remaining_time = "> 1 year"

        print "%s, %.2f TB, %.2f TB, %d%%, %s" % \
            (series, 
             r_val['latest_used'] / (2**40),
             r_val['latest_remaining'] / (2**40),
             r_val['percent_used'],
             remaining_time)


if __name__ == '__main__':
    sys.exit(main())

# vim: et:ai:sw=4:ts=4
