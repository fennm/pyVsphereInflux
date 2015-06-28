from pyVsphereInflux import InfluxResult
from influxdb.influxdb08 import InfluxDBClient

def write_results(dsn, results):
    """Connect to an InfluxDB instance and write results to it
            Arguments:
                dsn: an InflxDBClient DSN, for example:
                    influxdb://username:password@localhost:8086/database
                results: a list of InfluxResult objects
    """
    client = InfluxDBClient.from_DSN(dsn)
    raw_dicts = [x.to_dict() for x in results]
    client.write_points(raw_dicts)

# vim: et:ai:sw=4:ts=4
