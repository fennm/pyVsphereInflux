class InfluxResult(object):
    def __init__(self, measurement, tags=None, timestamp=None, fields=None):
        self.measurement = measurement

        self.tags = {}
        if tags:
            self.tags = tags

        self.timestamp = timestamp

        self.fields = {}
        if fields:
            self.fields = fields

    def __repr__(self):
        return repr(self.to_dict())

    def to_dict(self):
        """Convert to a dictionary as expected by the influxdb 0.9 module"""
        ret = {}
        ret['measurement'] = self.measurement
        ret['tags'] = self.tags
        ret['fields'] = self.fields
        if self.timestamp:
            ret['timestamp'] = self.timestamp

        return ret

class InfluxResult08(InfluxResult):
    @staticmethod
    def from_query(query_res):
        """Create InfluxResult08 objects from the return value of
           InfluxDBClient.query().  Since search result can have multiple
           points, returns a list of InfluxResult08 objects"""
        ret = []
        for series in query_res:
            for row in series['points']:
                ts = InfluxResult08(series['name'])

                for i in range(len(series['columns'])):
                    if series['columns'][i] == 'time':
                        ts.timestamp = row[i]
                    elif series['columns'][i] == 'sequence_number':
                        continue
                    else:
                        ts.fields[series['columns'][i]] = row[i]

                ret.append(ts)

        return ret


    def to_dict(self):
        """Convert to a dictionary as expected by the influxdb 0.8 module"""
        ret = {}

        ret['name'] = self.measurement

        ret['columns'] = []
        ret['points'] = [[]]

        # we only write a single timestamp per object, so the influx db
        # list of data (2-d array) will always only have one row
        for key in self.fields:
            ret['points'][0].append(self.fields[key])
            ret['columns'].append(key)

        for key in self.tags:
            ret['points'][0].append(self.tags[key])
            ret['columns'].append(key)

        if self.timestamp:
            ret['points'][0].insert(0, self.timestamp)
            ret['columns'].insert(0, "time")

        return ret

# vim: et:ai:sw=4:ts=4
