from influxdb.influxdb08 import InfluxDBClient
from pyVsphereInflux import InfluxResult08

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

def find_first_point(dsn, search, interval=None):
    """Connect to an InfluxDB instance and find the first point in each series
       optionally within the given intervala
            Arguments:
                dsn: an InflxDBClient DSN, for example:
                    influxdb://username:password@localhost:8086/database
                search: series name or regex to search against
                interval: length of history to search
            Return: A list of InfluxResult objects representing the points
    """
    client = InfluxDBClient.from_DSN(dsn)

    if interval is not None:
        where = "WHERE time > now() - %s" % (interval)
    else:
        where = ""
    query = "SELECT * FROM %s %s LIMIT 1 ORDER ASC" % \
            (search, where)
    query_res = client.query(query)
    result_objs = InfluxResult08.from_query(query_res)

    return result_objs

# vim: et:ai:sw=4:ts=4
