# pyVsphereInflux
A library and supporting script for pulling data from vSphere and inserting it into InfluxDB

Example usage:

    vsphere-influxdb-import.py --vcenter myvcenter --vs-username Administrator --vs-password password --influx-dsn influxdb://root:root@localhost:8086/vms

    $ vsphere-influxdb-import.py -h
    usage: vsphere-influxdb-import.py [-h] --vcenter VCENTER
				      [--vs-username VS_USERNAME]
				      [--vs-password VS_PASSWORD]
				      [--vs-port VS_PORT]
				      [--influx-dsn INFLUX_DSN] [--debug]

    collect metrics from vSphere and import into InfluxDB

    optional arguments:
      -h, --help            show this help message and exit
      --vcenter VCENTER     vCenter to connect to
      --vs-username VS_USERNAME
			    vSphere username
      --vs-password VS_PASSWORD
			    vSphere password
      --vs-port VS_PORT     vSphere port
      --influx-dsn INFLUX_DSN
			    InfluxDB DSN, eg.
			    influxdb://root:root@localhost:8086/database
      --debug, -d           enable debugging

