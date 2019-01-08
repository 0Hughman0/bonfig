import functools
import itertools
import sys
import collections

from bonfig.fields import Field, Store, Section


class BonfigType(type):

    def __new__(cls,  name, bases, attrs, **kwargs):
        attrs['__fields__'] = collections.defaultdict(list)
        attrs['__stores__'] = set()
        return super().__new__(cls, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, **kwargs):
        if sys.version_info[1] < 6: # Backport of __set_name__ from 3.6 :)
            for k, v in attrs.items():
                if isinstance(v, (Field, Store, Section)):
                    v.__set_name__(cls, k)

        fields = collections.defaultdict(list)
        stores = set()

        # Allow for inheritance
        for attr in itertools.chain(*(base.__dict__.values() for base in bases)):
            if isinstance(attr, Field):
                fields[attr.store_attr].append(attr)
            if isinstance(attr, Store):
                stores.add(attr)

        for attr in attrs.values():
            if isinstance(attr, Field):
                fields[attr.store_attr].append(attr)
            if isinstance(attr, Store):
                stores.add(attr)

        attrs['__fields__'].update(fields)
        attrs['__stores__'].update(stores)
        super().__init__(name, bases, attrs)


class Bonfig(metaclass=BonfigType):
    """
    Base class for all Bonfigs!

    Note
    ----
    If subclassing Bonfig and overwriting `__init__` ensure you call `super().__init__()` or the the Stores won't
    initialise properly!
    """

    def __init__(self, locked=False, *args, **kwargs):
        self._locked = False

        self.load(*args, **kwargs)

        if any(isinstance(getattr(self, store.name), Store) for store in self.__stores__):
            raise ValueError("Not all store attrs have been set during Bonfig.load")

        for store_attr, field_list in self.__fields__.items():

            for field in field_list:
                field.initialise(self)

        self._locked = locked

    def load(self, *args, **kwargs):
        pass

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
