#!/usr/bin/env python
# synthesize zero-sized data points for vm growth tracking
import sys
import argparse

from copy import copy
from pyVsphereInflux import InfluxResult08
from pyVsphereInflux.influx import write_results, find_first_point
from pyVsphereInflux.tools.regex import convert_to_alnum

influx_dsn_default="influxdb://root:root@localhost:8086/database"
data_fields = ['config.hardware.numCPU',
               'config.hardware.memoryMB',
               'summary.storage.committed']

def main():
    # take some input 
    parser = argparse.ArgumentParser(description="synthesize zero-sized data points for vm growth tracking")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--search-interval', default=None,
                        help="Length of time to search (e.g. 10m, 4h, 30d)")
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    # find the first point in each series within the last search interval
    search = "/vmprop.*/"
    first_points = find_first_point(args.influx_dsn, search, 
                               interval=args.search_interval)

    synth_points = []
    for ts in first_points:
        # whether we need to synthesize a zero point or not
        needs_synth = False
        for field in data_fields:
            if ts.fields[field] != 0:
                needs_synth = True

        if needs_synth:
            synth_ts = InfluxResult08(ts.measurement)
            synth_ts.timestamp = ts.timestamp - 600 # 10 minutes into the past
            synth_ts.fields = copy(ts.fields)
            synth_ts.tags = copy(ts.tags)
            for field in data_fields:
                synth_ts.fields[field] = 0

            synth_points.append(synth_ts)

    if args.debug:
        print "Synthesized points:"
        for ts in synth_points:
            print "Measurement:", ts.measurement
            print "Tags:", ts.tags
            print "Fields:", ts.fields
            print "Timestamp:", ts.timestamp
            print
    else:
        write_results(args.influx_dsn, synth_points)


if __name__ == '__main__':
    sys.exit(main())

# vim: et:ai:sw=4:ts=4
