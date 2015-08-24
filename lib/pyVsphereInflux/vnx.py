"""Tools for connecting to VNX and collecting data using naviseccli"""
import sys
import re
from subprocess import check_output

import pyVsphereInflux.tools.humanreadable as hr
from pyVsphereInflux import InfluxResult08
from pyVsphereInflux.tools.regex import convert_to_alnum

        
def build_vnx(vnx, tags, fields, measurement='vnxprop', args=None):
    """Build a list of InfluxResult objects
            Arguments:
                vnx: the hostname of a VNX SP to connect to
                tags: a list of VNX properties to use as Influx tags
                fields: a list of VNX propertries to use as Influx fields
                measurement: the influx db measurement name to use
                args: a argparse Namespace with the 
                      vnx_{username,password} fields
            Results:
                A list of InfluxResult objects suitable to insert into a
                database.
    """
    res = []

    # run the naviseccli command 
    # assumes that it is in the PATH
    cmd = ["naviseccli", "-User", args.vnx_username, 
                         "-Password", args.vnx_password,
                         "-Scope", "0",
                         "-h", vnx,
                         "storagepool", "-list", "-capacities", "-luns"]
    naviout = check_output(cmd)

    # build the result data structures
    recs = []
    data = {}
    for line in naviout.splitlines():
        # skip whitespace and blank lines
        if line == "" or line.isspace():
            continue

        # colon-delimited key value pairs
        key, value = line.split(":", 2)

        key = convert_to_alnum(key.strip())
        value = value.strip()

        # Pool Name signals the start of a new record, so push the current
        # record onto the list if we parsed anything from it
        if key == "Pool_Name" and len(data.keys()) > 0:
            recs.append(data)
            data = {}

        if key == "LUNs":
            # LUNs are logically a list
            value = value.split(",")
            # synthesize a LUN_Count field
            data["LUN_Count"] = len(value)
        # try to convert to numbers
        elif value.isdigit():
            value = int(value)
        elif re.match(r'[0-9]+\.[0-9]*', value):
            value = float(value)
        elif value.endswith(hr.SYMBOLS):
            value = hr.human2bytes(value)
        else:
            value = convert_to_alnum(value.strip())

        data[key] = value
            
    # grab the final record
    if len(data.keys()) > 0:
        recs.append(data)

    for data in recs:
        missing_data = False
        meas = "%s.%s" % (measurement, convert_to_alnum(data['Pool_Name']))
        ts = InfluxResult08(meas)
        for tag in tags:
            try:
                ts.tags[tag] = data[tag]
            except KeyError as e:
                print "Could not process %s for data %s" % (tag, data['name'])
                missing_data = True
        for field in fields:
            try:
                ts.fields[field] = data[field]
            except KeyError as e:
                print "Could not process %s for data %s" % (field, data['name'])
                missing_data = True

        ts.tags['vnx'] = vnx

        if not missing_data:
            res.append(ts)

    return res

# vim: et:ai:sw=4:ts=4
