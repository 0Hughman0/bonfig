import itertools
import sys
from abc import abstractmethod, ABC
import collections
import functools


class BaseField(ABC):
    """
    Bonfig Field Base class representing a parameter from your configuration. This object encapsulates how this
    parameter is serialised and deserialsed.

    Attributes
    ----------
    _store_attr : str
        name of attribute to access Store for fields of this type within the config
    """

    _store_attr = None

    @abstractmethod
    def create_store(self, parent):
        """
        Hook to control the data Store type for this.

        Returns
        -------
        store : obj
            subclass of `BaseIOStore` for storing data in.
        """
        pass

    @abstractmethod
    def initialise(self, bonfig):
        """
        Hook for controlling the initialisation of the field.
        """
        pass

    def pre_set(self, val):
        """
        Apply function to values before they are inserted into data Store
        """
        return val

    def post_get(self, val):
        """
        Apply function to values after they are fetched from data Store
        """
        return val

    @abstractmethod
    def _get_value(self, store):
        """
        Hook to allow you to control how the value is looked up in the data Store

        Note
        ----
        `self._post_get` is called _after_ this is called... is that obvious?
        """
        pass

    @abstractmethod
    def _set_value(self, store, value):
        """
        Hook to allow you to control how values are set in the data Store.

        Note
        ----
        `self._pre_set` is called _before_ this is called. (additionally, a check for the locked state of the bonfig
        is made (see `self.__set__` implementation).
        """
        pass

    def _check_lock(self, bonfig):
        if bonfig.locked:
            raise RuntimeError("Attempting to mutate a locked Bonfig")

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        store = getattr(instance, self._store_attr)
        return self.post_get(self._get_value(store))

    def __set__(self, instance, value):
        self._check_lock(instance)
        store = getattr(instance, self._store_attr)
        self._set_value(store, self.pre_set(value))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._store_attr)


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

        attrs['fields'] = fields

        return super().__new__(mcs, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs, **kwargs):
        if sys.version_info[1] < 6: # Backport of __set_name__ from 3.6 :)
            for k, v in attrs.items():
                if isinstance(v, BaseField):
                    v.__set_name__(cls, k)
        super().__init__(name, bases, attrs)


class BaseIOStore(ABC):

    def __init__(self, parent):
        self.parent = parent

    @staticmethod
    def _method_chainify(is_func=False):
        def outer(m):
            @functools.wraps(m)
            def wrapped(self, *args, **kwargs):
                if is_func:
                    m(*args, **kwargs)
                else:
                    m(self, *args, **kwargs)
                return self.parent
            return wrapped
        return outer

    @abstractmethod
    def read(self, *args, **kwargs):
        pass


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

        for store_attr, field_list in self.fields.items():
            setattr(self, store_attr, field_list[0].create_store(self))

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


def make_sub_field(name, post_get, pre_set, bases=None):
    """
    Factory function for producing `Field`-like classes.

    Parameters
    ----------
    name : str
        Name of new field class
    post_get : func
        Function to apply to values just after they are fetched from the data Store.
    pre_set : func
        Function to apply to values just before they are inserted into the data Store.
    bases : cls
        Class for the newly created class to subclass (defaults to `Field`).

    Returns
    -------
    cls : cls
        New Field subclass.

    Example
    -------
    >>> IntField = make_sub_field('IntField', int, str)
    """
    cls = type(name, (bases,), {})
    cls.post_get = lambda s, v: post_get(v)
    cls.pre_set = lambda s, v: pre_set(v)
    return cls


class FieldDict(dict):
    """
    Subclass of dict for storing field classes.
    """
    def __init__(self, bases, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.bases = bases
        self.add(bases)

    def add(self, field):
        """
        Add a field class to a field dict. This method implicitly uses `field.__name__` as the key.

        Example
        -------
        >>> from bonfig import INIfields
        >>> @INIfields.add
        >>> class TimeField(Field):
        >>>     def post_get(self, val):
        >>>         return datetime.time(int(val))
        >>>     def pre_set(self, val):
        >>>         return str(val.hour)

        Parameters
        ----------
        field : cls
            A field class that you want to be added to the dict

        Returns
        -------
        field : cls
            Returns the same field instance back. This allows the method to be used as a class decorator!
        """
        self[field.__name__] = field
        return field

    def make_quick(self, name, post_get, pre_set):
        """
        Factory function for producing `Field`-like classes.

        Parameters
        ----------
        post_get : func
            Function to apply to values just after they are fetched from the data Store.
        pre_set : func
            Function to apply to values just before they are inserted into the data Store.
        bases : cls
            Class for the newly created class to subclass (defaults to `Field`).

        Returns
        -------
        cls : cls
            New Field subclass.

        Note
        ----
        Created classes are implicitly inserted into the FieldDict

        Example
        -------
        >>> IntField = fields.make_quick('IntField', int, str)
        """
        cls = make_sub_field(name, post_get, pre_set, self.bases)
        self.add(cls)
        return cls
