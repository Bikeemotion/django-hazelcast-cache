=====
Django Hazelcast Cache
=====


`django-hazelcast-cache`_ is a cache backend for the `Django`_ webframework.  It
uses the `hazelcast`_ server.


Quick Start
===========


**Recommended:**

* `hazelcast-python-client`_ >= 3.7.2

* `python`_ >= 2.7


1. Install `hazelcast`_ server instance.

2. Run ``pip install django-hazelcast-cache``.

3. Modify your Django settings to use ``hazelcast_cache``.

.. code:: python

    CACHES = {
        'default': {
            'BACKEND': 'hazelcast_cache.HazelcastCache',
            'LOCATION': 'localhost:5701',
            'OPTIONS': {
                'GROUP_NAME': 'dev',
                'GROUP_PASSWORD': 'dev-pass',
                'MAP_KEY': 'test'
            },
        },
    }

.. _Django: https://www.djangoproject.com/
.. _hazelcast-python-client: https://github.com/hazelcast/hazelcast-python-client/
.. _hazelcast: https://hazelcast.com/
.. _python: http://python.org
.. _Memcached: http://memcached.org
