#!/usr/bin/env python
# collect metrics from VNX and import into InfluxDB
# requires naviseccli and assumes it is in the path
import sys
import argparse

from pyVsphereInflux.vnx import build_vnx
from pyVsphereInflux.influx import write_results
from pyVsphereInflux.tools.regex import convert_to_alnum

influx_dsn_default="influxdb://root:root@localhost:8086/database"

vnx_tags = ['Pool_Name',
            'Pool_ID']
vnx_fields = ['LUN_Count',
             'User_Capacity__GBs_',
             'Consumed_Capacity__GBs_',
             'Total_Subscribed_Capacity__GBs_']
def main():
    # take some input 
    parser = argparse.ArgumentParser(description="collect metrics from VNX and import into InfluxDB.  Assumes naviseccli is in the PATH")
    parser.add_argument('--vnx', required=True, action='append', 
                        help="VNX SP to connect to")
    parser.add_argument('--vnx-username', default="admin", 
                        help="navisec username")
    parser.add_argument('--vnx-password', default="changeme", 
                        help="navisec password")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    # loop over vCenters and collect metrics
    for vnx in args.vnx:

        meas = "vnxprop.%s" % (convert_to_alnum(vnx))
        results = build_vnx(vnx, vnx_tags, vnx_fields, 
                            measurement=meas, args=args)
        
        if args.debug:
            print "Results of VNX query:"
            for ts in results:
                print "Measurement:", ts.measurement
                print "Tags:", ts.tags
                print "Fields:", ts.fields
                print
        else:
            write_results(args.influx_dsn, results)

if __name__ == '__main__':
    sys.exit(main())

# vim: et:ai:sw=4:ts=4
