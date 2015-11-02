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
from pyVsphereInflux import InfluxResult08
from pyVsphereInflux.vsphere import build_vmresultset
from pyVsphereInflux.influx import write_results
from pyVsphereInflux.tools.regex import convert_to_alnum

influx_dsn_default = "influxdb://root:root@localhost:8086/database"
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

def agg_by_vcenter(results):
    # agg_toplevelfolder is dictionary whose values are
    # InfluxResults
    # agg_vcenter['vcenter']
    agg_vcenter = {}
    meas_base = "vmagg_vcenter"
    for ts in results:
        vcenter = convert_to_alnum(ts.tags['vcenter'])

        # new vcenter, which means new aggregrate
        if vcenter not in agg_vcenter:
            agg_obj = InfluxResult08("%s.%s" % (meas_base, vcenter))
            for tag in ['vcenter']:
                agg_obj.tags[tag] = ts.tags[tag]
            for field in ts.fields:
                agg_obj.fields[field] = ts.fields[field]
            agg_obj.timestamp = ts.timestamp
            agg_vcenter[vcenter] = agg_obj
        else:
            agg_obj = agg_vcenter[vcenter]
            # aggregate on fields
            for field in ts.fields:
                if field not in agg_obj.fields:
                    agg_obj.fields[field] = ts.fields[field]
                elif type(agg_obj.fields[field]) in (int, long, float):
                    agg_obj.fields[field] += ts.fields[field]

    # now flatten to a list
    ret = []
    for vcenter in agg_vcenter:
        ret.append(agg_vcenter[vcenter])

    return ret

def agg_by_topLevelFolder(results):
    # agg_toplevelfolder is a set of nested dictionaries whose values are
    # InfluxResults
    # agg_toplevelfolder['vcenter']['datacenter']['afolder']
    agg_topLevelFolder = {}
    meas_base = "vmagg_topLevelFolder"
    for ts in results:
        vcenter = convert_to_alnum(ts.tags['vcenter'])
        datacenter = convert_to_alnum(ts.tags['datacenter'])
        topLevelFolder = convert_to_alnum(ts.tags['topLevelFolder'])

        # new vcenter
        if vcenter not in agg_topLevelFolder:
            agg_topLevelFolder[vcenter] = {}

        # new datacenter 
        if datacenter not in agg_topLevelFolder[vcenter]:
            agg_topLevelFolder[vcenter][datacenter] = {}

        # new topLevelFolder, which means new aggregrate
        if topLevelFolder not in agg_topLevelFolder[vcenter][datacenter]:
            agg_obj = InfluxResult08("%s.%s.%s.%s" % \
                (meas_base, vcenter, datacenter, topLevelFolder))
            for tag in ['vcenter', 'datacenter', 'topLevelFolder']:
                agg_obj.tags[tag] = ts.tags[tag]
            for field in ts.fields:
                agg_obj.fields[field] = ts.fields[field]
            agg_obj.timestamp = ts.timestamp
            agg_topLevelFolder[vcenter][datacenter][topLevelFolder] = agg_obj
        else:
            agg_obj = agg_topLevelFolder[vcenter][datacenter][topLevelFolder] 
            # aggregate on fields
            for field in ts.fields:
                if field not in agg_obj.fields:
                    agg_obj.fields[field] = ts.fields[field]
                elif type(agg_obj.fields[field]) in (int, long, float):
                    agg_obj.fields[field] += ts.fields[field]

    # now flatten to a list
    ret = []
    for vcenter in agg_topLevelFolder:
        for datacenter in agg_topLevelFolder[vcenter]:
            for topLevelFolder in agg_topLevelFolder[vcenter][datacenter]:
                ret.append(
                    agg_topLevelFolder[vcenter][datacenter][topLevelFolder])

    return ret

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
            if len(ts.tags['folderPath'].split('/')) >= 2:
                ts.tags['topLevelFolder'] = ts.tags['folderPath'].split('/')[1]
            else:
                ts.tags['topLevelFolder'] = "None"

        # collect the results and some aggregates 
        output = []
        output.extend(results)
        output.extend(agg_by_topLevelFolder(results))
        output.extend(agg_by_vcenter(results))

        # now write the output to the database
        if args.debug:
            print "Results of vSphere query:"
            for ts in output:
                print "Measurement:", ts.measurement
                print "Tags:", ts.tags
                print "Fields:", ts.fields
                print
        else:
            write_results(args.influx_dsn, output)

if __name__ == '__main__':
    sys.exit(main())

# vim: et:ai:sw=4:ts=4
