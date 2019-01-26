import sys
import types

from bonfig.fields import Field, Store, Section


class BonfigType(type):
    """
    Metaclass for Bonfig base class.

    Facilitates the loading of Fields into class attributes, which is in turn used by the Bonfig `__init__` to
    initialise `Field` values.

    Additionally back-ports `__set_name__` behaviour from 3.6 that's extensively used.
    """

    def __new__(mcs, name, bases, attrs, **kwargs):
        """Creates Bonfig class type

        """
        attrs['__fields__'] = set()
        attrs['__store_attrs__'] = set()
        return super().__new__(mcs, name, bases, attrs, **kwargs)

    def __init__(cls, name, bases, attrs):
        """Initialises Bonfig class type.

        Uses built-in `dir` to get attributes of base-classes.
        """
        if sys.version_info[1] < 6:  # Backport of __set_name__ from 3.6 :)
            for k, v in attrs.items():
                if isinstance(v, (Field, Store, Section)):
                    v.__set_name__(cls, k)

        fields = attrs['__fields__']
        stores = attrs['__store_attrs__']

        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Field):
                fields.add(attr)
                stores.add(attr.store_attr)

        super().__init__(name, bases, attrs)


def _freeze_mapping(d):
    """Recursively turn mapping into nested `types.MappingProxyTypes`

    """
    d = dict(d)
    for k in d.keys():
        if hasattr(d[k], '__getitem__') and hasattr(d[k], 'keys'):
            d[k] = _freeze_mapping(d[k])
    d = types.MappingProxyType(d)
    return d


class Bonfig(metaclass=BonfigType):
    """
    Base class for all Bonfigs.

    Parameters
    ----------
    frozen : bool, optional
        Freeze Bonfig just after initialisation - by calling :py:meth:`Bonfig.freeze`.
    *args
        Positional arguments, passed to :py:meth:`Bonfig.load`.
    **kwargs
        Keyword arguments, passed to :py:meth:`Bonfig.load`.

    Notes
    -----
    Instances of this class shouldn't be created directly, instead it should be subclassed (see examples).

    Ideally do overwrite or call `__init__` directly, instead use the provided load hook for
    initialising things like data stores.

    Attributes
    ----------
    __fields__ : set
        a `set` containing all the classes `Field` attributes.
    __store_attrs__ : set
        a `set` containing the names of each store attribute for that class

    Examples
    --------

    """

    def __init__(self, *args, frozen=True, **kwargs):
        self.load(*args, **kwargs)

        for field in self.__fields__:
            field._initialise(self)

        if frozen:
            self.freeze()

    def load(self, *args, **kwargs):
        """
        Hook called during initialisation for loading store attributes.

        Is basically `__init__`, but called at the right time such that locking works and that fields can be
        initialised.

        Notes
        -----
        As `load` is called before `Field`s are initialised, values can be overwritten by fields unless
        `Field.val=None`.

        Parameters
        ----------
        *args
            args from `__init__`
        **kwargs
            kwargs from `__init__`
        """
        for store_attr in self.__store_attrs__:
            setattr(self, store_attr, {})

    def freeze(self):
        """Freeze Bonfig stores.

        Works by creating a copy of each store as dict, then converting to an `MappingProxyType`.

        Notes
        -----
        In order to 'freeze' your store, it each container needs to implement both `__getitem__()` and `keys()` as a
        minimum.
        """
        for store_attr in self.__store_attrs__:
            frozen = _freeze_mapping(getattr(self, store_attr))
            setattr(self, store_attr, frozen)
