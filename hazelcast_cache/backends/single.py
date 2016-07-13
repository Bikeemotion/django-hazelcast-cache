import random

from hazelcast_cache.backends.base import BaseHazelcastCache, DEFAULT_TIMEOUT


class HazelcastCache(BaseHazelcastCache):

    def __init__(self, server, params):
        """
        Connect to Hazelcast, and set up cache backend.
        """
        super(HazelcastCache, self).__init__(server, params)
        self.master_client = self.get_client(None)

    def get_client(self, key, write=False):
        return self.client

    ####################
    # Django cache api #
    ####################

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs. This is much more efficient than calling set() multiple times.
        If timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.
        """

        versioned_keys = self.make_keys(data.keys(), version=version)
        new_data = {}
        for key in versioned_keys:
            new_data[key] = self.prep_value(data[key._original_key])
        return self._set_many(self.master_client, new_data)

    def get_many(self, keys, version=None):
        versioned_keys = self.make_keys(keys, version=version)
        return self._get_many(self.master_client, keys, versioned_keys=versioned_keys)

    def delete_many(self, keys, version=None):
        """Remove multiple keys at once."""
        versioned_keys = self.make_keys(keys, version=version)
        if versioned_keys:
            self._delete_many(self.master_client, versioned_keys)

