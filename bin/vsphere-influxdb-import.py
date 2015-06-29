#!/usr/bin/env python
# collect metrics from vSphere and import into InfluxDB
import sys
import argparse
import time 
import atexit
import requests
import ssl

from pyVim import connect
from pyVmomi import vim
from pyVsphereInflux.vsphere import build_vmresultset
from pyVsphereInflux.influx import write_results
from pyVsphereInflux.tools.regex import convert_to_alnum

influx_dsn_default="influxdb://root:root@localhost:8086/database"
vm_tags = ['name']
vm_fields = ['config.hardware.numCPU',
             'config.hardware.memoryMB',
             'guest.guestState',
             'summary.storage.committed']

def silence_warnings():
    """disable warnings from requests version of urllib3"""

    requests.packages.urllib3.disable_warnings()
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

def main():
    # take some input 
    parser = argparse.ArgumentParser(description="collect metrics from vSphere and import into InfluxDB")
    parser.add_argument('--vcenter', required=True, action='append', 
                        help="vCenter to connect to")
    parser.add_argument('--vs-username', default="admin", 
                        help="vSphere username")
    parser.add_argument('--vs-password', default="changeme", 
                        help="vSphere password")
    parser.add_argument('--vs-port', type=int, default=443, 
                        help="vSphere port")
    parser.add_argument('--influx-dsn', default=influx_dsn_default,
                        help="InfluxDB DSN, eg. %s" % influx_dsn_default)
    parser.add_argument('--debug', '-d', action='store_true', 
                        help="enable debugging")

    args = parser.parse_args()

    silence_warnings()

    # loop over vCenters and collect metrics
    for vcenter in args.vcenter:
        service_instance = None

        try:
            service_instance = connect.SmartConnect(host=vcenter,
                                                    user=args.vs_username,
                                                    pwd=args.vs_password,
                                                    port=args.vs_port)
            atexit.register(connect.Disconnect, service_instance)
        except Exception as e:
            print "Unable to connect to %s" % vcenter
            continue

        meas = "vmprop.%s" % (convert_to_alnum(vcenter))
        results = build_vmresultset(service_instance, vm_tags, vm_fields,
                                    measurement=meas)
        
        for ts in results:
            ts.tags['vcenter'] = vcenter
            ts.tags['topLevelFolder'] = ts.tags['folderPath'].split('/')[1]
        
        if args.debug:
            print "Results of vSphere query:"
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
