try:
    import importlib
except ImportError:
    from django.utils import importlib

from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import smart_text, smart_bytes


def import_class(path):
    module_name, class_name = path.rsplit('.', 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        raise ImproperlyConfigured('Could not find module "%s"' % module_name)
    else:
        try:
            return getattr(module, class_name)
        except AttributeError:
            raise ImproperlyConfigured('Cannot import "%s"' % class_name)


class CacheKey(object):
    """
    A stub string class that we can use to check if a key was created already.
    """
    def __init__(self, key, versioned_key):
        self._original_key = key
        self._versioned_key = versioned_key

    def __eq__(self, other):
        return self._versioned_key == other

    def __unicode__(self):
        return smart_text(self._versioned_key)

    def __hash__(self):
        return hash(self._versioned_key)

    __repr__ = __str__ = __unicode__