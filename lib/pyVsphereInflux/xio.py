"""Tools for connecting to XtremIO and collecting data"""
import sys
import pexpect

import pyVsphereInflux.tools.humanreadable as hr

from pyVsphereInflux import InfluxResult08
from pyVsphereInflux.tools.regex import convert_to_alnum

        
def build_xiocluster(xms, tags, fields, measurement='xioprop', args=None):
    """Build a list of InfluxResult objects
            Arguments:
                xms: the hostname of an XtremIO XMS to connect to
                tags: a list of VM properties to use as Influx tags
                fields: a list of VM propertries to use as Influx fields
                measurement: the influx db measurement name to use
                args: a argparse Namespace with the 
                      {xmsadmin,xms}_{username,password} fields
            Results:
                A list of InfluxResult objects suitable to insert into a
                database.
    """
    res = []

    # set up some logging if we run in debug mode
    pxlogfile = None
    if args.debug:
        pxlogfile = sys.stdout

    # do the first xmsadmin ssh login
    ssh_cmd = "ssh -oStrictHostKeyChecking=no -l %s %s" % \
                (args.xmsadmin_username, xms)
    p = pexpect.spawn(ssh_cmd, logfile=pxlogfile)
    p.expect ("password:")
    p.sendline(args.xmsadmin_password)

    # do the secondary user login (yes XtremIO is wierd)
    p.expect("Username:")
    p.sendline(args.xms_username)
    p.expect("Password:")
    p.sendline(args.xms_password)

    # check for a prompt and enter commands
    prompt = r"xmcli \(%s\)>" % args.xms_username
    p.expect(prompt)
    p.sendline("show-clusters")
    p.expect(prompt)
    clusterout = p.before
    p.close()

    # insert a newline into the debug output for clarity
    if args.debug:
        print

    header = None
    for line in clusterout.splitlines():
        # the command being echoed
        if "show-clusters" in line:
            continue
        # the header with a list of fields
        if line.startswith("Cluster-Name"):
            header = line.split()
            continue

        # a data row, parse into adict
        row = line.split()
        data = {}
        for i in range(len(row)):
            data[header[i]] = row[i]
        
        # build the result object
        missing_data = False
        meas = "%s.%s" % (measurement, convert_to_alnum(data['Cluster-Name']))
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

            # try to convert to numbers
            if data[field].isdigit():
                ts.fields[field] = int(data[field])
            elif data[field].endswith(hr.SYMBOLS):
                ts.fields[field] = hr.human2bytes(data[field])

        ts.tags['xms'] = xms

        if not missing_data:
            res.append(ts)

    return res

# vim: et:ai:sw=4:ts=4
