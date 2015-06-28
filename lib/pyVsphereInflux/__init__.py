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
        """Convert to a dictionary as expected by the influxdb module"""
        ret = {}
        ret['measurement'] = self.measurement
        ret['tags'] = self.tags
        ret['fields'] = self.fields
        if self.timestamp:
            ret['timestamp'] = self.timestamp

        return ret

# vim: et:ai:sw=4:ts=4
