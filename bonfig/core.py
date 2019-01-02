import itertools
import sys
import collections
import os
from types import SimpleNamespace

from bonfig.fields.base import BaseField
from .stores.json import JSONStore
from .stores.ini import INIStore


class BonfigStores(SimpleNamespace):

    def __call__(self):
        return self.config


class BonfigType(type):

    def __new__(mcs, name, bases, attrs, **kwargs):

        fields = collections.defaultdict(list)

        for attr in attrs.values():
            if isinstance(attr, BaseField):
                fields[attr._store_attr].append(attr)

        # Allow for inheritance
        for attr in itertools.chain(*(base.__dict__.values() for base in bases)):
            if isinstance(attr, BaseField):
                fields[attr._store_attr].append(attr)

        attrs['__fields__'] = fields

        return super().__new__(mcs, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, **kwargs):
        if sys.version_info[1] < 6: # Backport of __set_name__ from 3.6 :)
            for k, v in attrs.items():
                if isinstance(v, BaseField):
                    v.__set_name__(cls, k)
        super().__init__(name, bases, attrs)


class Bonfig(metaclass=BonfigType):
    """
    Base class for all Bonfigs!

    Note
    ----
    If subclassing Bonfig and overwriting `__init__` ensure you call `super().__init__()` or the the Stores won't
    initialise properly!
    """

    def __init__(self, locked=False):
        self._locked = False

        self.stores = BonfigStores(config=self,
                                   d={},
                                   environ=os.environ,
                                   ini=INIStore(self),
                                   json=JSONStore(self))

        for store_attr, field_list in self.__fields__.items():

            for field in field_list:
                field.initialise(self)

        self._locked = locked

    @property
    def locked(self):
        return self._locked

    def lock(self):
        self._locked = True

    def unlock(self):
        self._locked = False

    def __enter__(self):
        self.unlock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock()
