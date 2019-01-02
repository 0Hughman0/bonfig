from abc import ABC, abstractmethod


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

    def get_store(self, bonfig):
        return getattr(bonfig.stores, self._store_attr)

    def _check_lock(self, bonfig):
        if bonfig.locked:
            raise RuntimeError("Attempting to mutate a locked Bonfig")

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def __get__(self, bonfig, owner):
        if bonfig is None:
            return self
        store = self.get_store(bonfig)
        return self.post_get(self._get_value(store))

    def __set__(self, bonfig, value):
        self._check_lock(bonfig)
        store = self.get_store(bonfig)
        self._set_value(store, self.pre_set(value))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._store_attr)


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


def str_bool(t):
    return t != 'False'
