# pyVsphereInflux
A library and supporting script for pulling data from vSphere and inserting it into InfluxDB

Example usage:

    vsphere-influxdb-import.py --vcenter myvcenter --vs-username Administrator --vs-password password --influx-dsn influxdb://root:root@localhost:8086/vms
