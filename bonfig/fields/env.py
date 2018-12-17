import os

from ..core import BaseField
from bonfig.core import make_sub_field


class EnvField(BaseField):
    """
    A config Field where it's value is looked up in your environment variables.

    Parameters
    ----------
    name : str
        name of environment variable to look up (optional - defaults to variable name assigned to)
    default : str
        fallback value if not found

    Notes
    -----
    Environment variables can also be set with this Field type.

    As the value is looked up every time, and is not stored in the data attr, for example when using PyBonfig, it's
    value won't be written to disk.
    """

    _store_attr = 'environ'

    def create_store(self, parent):
        return os.environ

    def __init__(self, name=None, default='', dynamic=False):
        if not isinstance(name, str) and name is not None:
            raise TypeError("Environment variable name must be a string!")

        self.name = name
        self.default = default
        self.dynamic = dynamic
        self._cache = None

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def initialise(self, bonfig):
        if not self.dynamic:
            self._cache = bonfig.environ.get(self.name, self.default)

    def _get_value(self, d):
        if not self.dynamic:
            return self._cache

        return d.get(self.name, default=self.default)

    def _set_value(self, store, value):
        if not self.dynamic:
            raise RuntimeError("Attempting to set value on non-dynamic environment variable")
        store.environ[self.name] = value


EnvIntField = make_sub_field('EnvIntField', int, str, bases=EnvField)
EnvFloatField = make_sub_field('EnvFloatField', float, str, bases=EnvField)
EnvBoolField = make_sub_field('EnvBoolField', bool, str, bases=EnvField)