import random

from hazelcast_cache.backends.base import BaseHazelcastCache


class HazelcastCache(BaseHazelcastCache):

    def __init__(self, server, params):
        """
        Connect to Hazelcast, and set up cache backend.
        """
        super(HazelcastCache, self).__init__(server, params)

    def get_client(self, key, write=False):
        return self.client

    ####################
    # Django cache api #
    ####################