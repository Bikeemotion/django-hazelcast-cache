from django.core.cache.backends.base import BaseCache, InvalidCacheBackendError
from django.core.exceptions import ImproperlyConfigured

import logging

try:
    import hazelcast
except ImportError:
    raise InvalidCacheBackendError(
        "Redis cache backend requires the 'hazelcast-python-client' library"
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

        #self.db = self.get_db()
        self.password = self.get_password()
        #self.parser_class = self.get_parser_class()
        #self.pickle_version = self.get_pickle_version()
        #self.socket_timeout = self.get_socket_timeout()
        #self.socket_connect_timeout = self.get_socket_connect_timeout()
        #self.connection_pool_class = self.get_connection_pool_class()
        #self.connection_pool_class_kwargs = (
        #    self.get_connection_pool_class_kwargs()
        #)

        # Serializer
        self.serializer_class = self.get_serializer_class()
        self.serializer_class_kwargs = self.get_serializer_class_kwargs()
        self.serializer = self.serializer_class(
            **self.serializer_class_kwargs
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

    def get_serializer_class(self):
        serializer_class = self.options.get(
            'SERIALIZER_CLASS',
            'redis_cache.serializers.PickleSerializer'
        )
        return import_class(serializer_class)

    def prep_value(self, value):
        return value


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

        return value

    def _set(self, client, key, value):
        my_map = client.get_map(self.map_key)

        print value

        return my_map.put(key, value)

    @get_client(write=True)
    def set(self, client, key, value, timeout=DEFAULT_TIMEOUT):
        """Persist a value to the cache, and set an optional expiration time.
        """

        result = self._set(client, key, self.prep_value(value))

        return result

    @get_client(write=True)
    def delete(self, client, key):
        """Remove a key from the cache."""
        return client.get_map(self.map_key).delete(key)

    def _delete_many(self, client, keys):
        return client.delete(*keys)

    def delete_many(self, keys, version=None):
        """
        Remove multiple keys at once.
        """
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

        # Only try to mget if we actually received any keys to get
        if map_keys:
            results = client.mget(versioned_keys)

            for key, value in zip(versioned_keys, results):
                if value is None:
                    continue
                recovered_data[map_keys[key]] = self.get_value(value)

        return recovered_data

    def get_many(self, keys, version=None):
        """Retrieve many keys."""
        raise NotImplementedError

    def _set_many(self, client, data):
        # Only call mset if there actually is some data to save
        if not data:
            return True
        return client.mset(data)

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

