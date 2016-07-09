try:
    import cPickle as pickle
except ImportError:
    import pickle

import json

try:
    import msgpack
except ImportError:
    pass

try:
    import yaml
except ImportError:
    pass


class BaseSerializer(object):

    def __init__(self, **kwargs):
        super(BaseSerializer, self).__init__(**kwargs)

    def serialize(self, value):
        raise NotImplementedError

    def deserialize(self, value):
        raise NotImplementedError


class JSONSerializer(BaseSerializer):

    def __init__(self, **kwargs):
        super(JSONSerializer, self).__init__(**kwargs)

    def serialize(self, value):
        return json.dumps(value)

    def deserialize(self, value):
        return json.loads(value)


class MSGPackSerializer(BaseSerializer):

    def serialize(self, value):
        return msgpack.dumps(value)

    def deserialize(self, value):
        return msgpack.loads(value, encoding='utf-8')


class YAMLSerializer(BaseSerializer):

    def serialize(self, value):
        return yaml.dump(value, encoding='utf-8')

    def deserialize(self, value):
        return yaml.load(value)


class DummySerializer(BaseSerializer):

    def __init__(self, **kwargs):
        super(DummySerializer, self).__init__(**kwargs)

    def serialize(self, value):
        return value

    def deserialize(self, value):
        return value