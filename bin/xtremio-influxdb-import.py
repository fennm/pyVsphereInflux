#!/usr/bin/env python
# collect metrics from XtremIO and import into InfluxDB
import sys
import argparse

from pyVsphereInflux.xio import build_xiocluster
from pyVsphereInflux.influx import write_results
from pyVsphereInflux.tools.regex import convert_to_alnum

influx_dsn_default = "influxdb://root:root@localhost:8086/database"

xio_tags = ['Cluster-Name']
xio_fields = ['Num-of-Vols',
             'Vol-Size',
             'UD-SSD-Space',
             'Logical-Space-In-Use',
             'UD-SSD-Space-In-Use']
def main():
    # take some input 
    parser = argparse.ArgumentParser(description="collect metrics from XtremIO and import into InfluxDB")
    parser.add_argument('--xms', required=True, action='append', 
                        help="XtremIO XMS to connect to")
    parser.add_argument('--xmsadmin-username', default="xmsadmin", 
                        help="xmsadmin username")
    parser.add_argument('--xmsadmin-password', default="changeme", 
                        help="xmsadmin password")
    parser.add_argument('--xms-username', default="admin", 
                        help="xms user username")
    parser.add_argument('--xms-password', default="changeme", 
                        help="xms user password")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    # loop over vCenters and collect metrics
    for xms in args.xms:

        meas = "xioprop.%s" % (convert_to_alnum(xms))
        results = build_xiocluster(xms, xio_tags, xio_fields, 
                                   measurement=meas, args=args)
        
        if args.debug:
            print "Results of XMS query:"
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
