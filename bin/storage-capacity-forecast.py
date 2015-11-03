#!/usr/bin/env python
# perform some forecasting based on storage usage data
import sys
import argparse
import time
import datetime

from influxdb.influxdb08 import InfluxDBClient
from pyVsphereInflux import InfluxResult08

influx_dsn_default = "influxdb://root:root@localhost:8086/database"
data_spec = { '/xioprop..*/': { 'used':     'UD-SSD-Space-In-Use',
                                'capacity': 'UD-SSD-Space' } 
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
                       WHERE time > now() - %s 
                       GROUP BY time(%s) ORDER ASC""" % \
                       (data_spec[list_spec]['used'], 
                        data_spec[list_spec]['capacity'],
                        series, args.range, args.interval)

            res = InfluxResult08.query(client, query)
            data_points[series] = res

    return data_points

def main():
    # take some input 
    parser = argparse.ArgumentParser(description="storage capacity forecasting based on influxdb data")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--range', default='120d',
                        help="Range of history to search (default: 120d)")
    parser.add_argument('--interval', default='1d',
                        help="Summarization interval for data points (default: 1d)")
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    data_points = get_raw_data(args)

    # compute regressions for the purposes of forecasting
    regressions = {}
    for series in data_points:
        x = [ts.timestamp for ts in data_points[series]]
        y = [ts.fields['used'] for ts in data_points[series]]
        m, b = basic_linear_regression(x, y)
        regressions[series] = (m, b)

    # come up with some useful results (forecasts)
    # y = m * x + b
    # x = time
    # y = used
    results = {}
    for series in regressions:
        latest_used = data_points[series][-1].fields['used']
        latest_cap = data_points[series][-1].fields['capacity']
        # what's the latest percentage used?
        percent_used = latest_used / latest_cap * 100
        # when will used intercept capacity?
        # set y = capacity, solve for x
        # (y - b) / m
        full_ts = (latest_cap - regressions[series][1]) / regressions[series][0]
        secs_until_full = full_ts - time.time()

        # stuff the results into a dict
        results[series] = {}
        results[series]['latest_used'] = latest_used
        results[series]['latest_capacity'] = latest_cap
        results[series]['percent_used'] = percent_used
        results[series]['full_ts'] = full_ts
        results[series]['secs_until_full'] = secs_until_full


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

    # print results
    print "Series, Capacity, Used, Percent Used, Date Full, Days Until Full"
    for series in results:
        r_val = results[series]
        print "%s, %.2f TB, %.2f TB, %.2f%%, %s, %d" % \
            (series, 
             r_val['latest_capacity'] / (2**40),
             r_val['latest_used'] / (2**40),
             r_val['percent_used'],
             datetime.date.fromtimestamp(r_val['full_ts']).strftime("%m-%d-%Y"),
             datetime.timedelta(seconds=r_val['secs_until_full']).days)


if __name__ == '__main__':
    sys.exit(main())

# vim: et:ai:sw=4:ts=4
