import logging

from django.core.cache.backends.base import BaseCache, InvalidCacheBackendError

from hazelcast_cache.utils import import_class, CacheKey

try:
    import hazelcast
except ImportError:
    raise InvalidCacheBackendError(
        "Hazelcast cache backend requires the 'hazelcast-python-client' library"
    )

from functools import wraps

logging.basicConfig(format='%(asctime)s%(msecs)03d [%(name)s] %(levelname)s: %(message)s', datefmt="%H:%M%:%S,")
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("main")

DEFAULT_TIMEOUT = 1000


def get_client(write=False):

    def wrapper(method):

        @wraps(method)
        def wrapped(self, key, *args, **kwargs):
            version = kwargs.pop('version', None)
            client = self.get_client(key, write=write)
            key = self.make_key(key, version=version)
            return method(self, client, key, *args, **kwargs)

        return wrapped

    return wrapper


class BaseHazelcastCache(BaseCache):

    def __init__(self, server, params):
        """
        Connect to Hazelcast, and set up cache backend.
        """
        super(BaseHazelcastCache, self).__init__(params)
        self.server = server
        self.params = params or {}
        self.options = params.get('OPTIONS', {})
        self.client = self.create_client()
        self.map_key = 'map'
        self.password = self.get_password()

        # Serializer
        self.serializer_class = self.get_serializer_class()
        self.serializer_class_kwargs = self.get_serializer_class_kwargs()
        self.serializer = self.serializer_class(
            **self.serializer_class_kwargs
        )

        # Compressor
        self.compressor_class = self.get_compressor_class()
        self.compressor_class_kwargs = self.get_compressor_class_kwargs()
        self.compressor = self.compressor_class(
            **self.compressor_class_kwargs
        )

    def get_password(self):
        return self.params.get('password', self.options.get('PASSWORD', None))

    def create_client(self):
        logging.basicConfig()
        logging.getLogger().setLevel(logging.WARNING)

        config = hazelcast.ClientConfig()
        config.group_config.name = "dev"
        config.group_config.password = "dev-pass"
        config.network_config.connection_attempt_limit = 1
        config.network_config.addresses.append('172.17.42.1:5701')

        client = hazelcast.HazelcastClient(config)

        return client

    def get_timeout(self, timeout):
        if timeout is DEFAULT_TIMEOUT:
            timeout = self.default_timeout

        if timeout is not None:
            timeout = int(timeout)

        return timeout

    def get_serializer_class(self):
        serializer_class = self.options.get(
            'SERIALIZER_CLASS',
            'hazelcast_cache.serializers.JSONSerializer'
        )
        return import_class(serializer_class)

    def get_serializer_class_kwargs(self):
        kwargs = self.options.get('SERIALIZER_CLASS_KWARGS', {})
        return kwargs

    def get_compressor_class(self):
        compressor_class = self.options.get(
            'COMPRESSOR_CLASS',
            'hazelcast_cache.compressors.NoopCompressor'
        )
        return import_class(compressor_class)

    def get_compressor_class_kwargs(self):
        return self.options.get('COMPRESSOR_CLASS_KWARGS', {})

    def prep_value(self, value):
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        value = self.serialize(value)
        return self.compress(value)

    def get_value(self, original):
        try:
            value = int(original)
        except (ValueError, TypeError):
            value = self.decompress(original)
            value = self.deserialize(value)
        return value

    def serialize(self, value):
        return self.serializer.serialize(value)

    def deserialize(self, value):
        try:
            value = self.serializer.deserialize(value)
        except:
            pass

        return value

    def compress(self, value):
        return self.compressor.compress(value)

    def decompress(self, value):
        return self.compressor.decompress(value)

    def make_key(self, key, version=None):
        if not isinstance(key, CacheKey):
            versioned_key = super(BaseHazelcastCache, self).make_key(key, version)
            return CacheKey(key, versioned_key)
        return key

    def make_keys(self, keys, version=None):
        return [self.make_key(key, version=version) for key in keys]


    ####################
    # Django cache api #
    ####################

    @get_client(write=True)
    def add(self, client, key, value):
        """Add a value to the cache, failing if the key already exists.
        Returns ``True`` if the object was added, ``False`` if not.
        """
        return self._set(client, key, self.prep_value(value))

    @get_client()
    def get(self, client, key, default=None):
        """Retrieve a value from the cache.
        Returns deserialized value if key is found, the default if not.
        """
        value = client.get_map(self.map_key).get(key).result()
        if value is None:
            return default

        return self.get_value(value)

    def _set(self, client, key, value, timeout):
        # https://github.com/hazelcast/hazelcast-python-client/blob/b033b8c26b4a932c84737a33f010d01b3910a87a/hazelcast/proxy/map.py
        return client.get_map(self.map_key).put(key, value, timeout)

    @get_client(write=True)
    def set(self, client, key, value, timeout=DEFAULT_TIMEOUT):
        """Persist a value to the cache, and set an optional expiration time.
        """

        result = self._set(client, key, self.prep_value(value), timeout)
        return result

    @get_client(write=True)
    def delete(self, client, key):
        """Remove a key from the cache."""
        return client.get_map(self.map_key).remove(key)

    def _delete_many(self, client, keys):
        for key in keys:
            client.get_map(self.map_key).remove(key)

        return

    def delete_many(self, keys, version=None):
        """Remove multiple keys at once."""

        raise NotImplementedError

    def _clear(self, client):
        raise NotImplementedError

    def clear(self, version=None):
        """Flush cache keys.
        If version is specified, all keys belonging the version's key
        namespace will be deleted.  Otherwise, all keys will be deleted.
        """
        raise NotImplementedError

    def _get_many(self, client, original_keys, versioned_keys):
        recovered_data = {}
        map_keys = dict(zip(versioned_keys, original_keys))

        # Only if we actually received any keys to get
        if map_keys:
            for key in versioned_keys:
                value = client.get_map(self.map_key).get(key).result()
                if value is None:
                    continue
                recovered_data[key] = self.get_value(value)

        return recovered_data

    def get_many(self, keys, version=None):
        """Retrieve many keys."""
        raise NotImplementedError

    def _set_many(self, client, data):
        # Only if there actually is some data to save
        if not data:
            return True

        for k, v in data.iteritems():
            client.get_map(self.map_key).put(k, v)

        return

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """Set a bunch of values in the cache at once from a dict of key/value
        pairs. This is much more efficient than calling set() multiple times.
        If timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.
        """
        raise NotImplementedError

    def incr(self, client, key, delta=1):
        raise NotImplementedError

    def _incr_version(self, client, old, new, delta, version):
        raise NotImplementedError

    def incr_version(self, key, delta=1, version=None):
        """Adds delta to the cache version for the supplied key. Returns the
        new version.
        """
        raise NotImplementedError

