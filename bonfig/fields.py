"""
Attributes
----------
fields : FieldDict
    A global `dict` -like object that stores all of the field classes. This dict is used to provide stores and sections
    with access to field classes, as such, add to this global dict to make custom fields available in that context. (By
    default includes `Field`, `IntField`, `FloatField`, `BoolField` and `DatetimeField`.
"""

import functools
import datetime


class Store:
    """
    Placeholder class, allowing structure of `store` to be created in `Bonfig`.

    Upon initialisation should be overwritten with an container object that supports `__getitem__` using
    :py:meth:`Bonfig.load`.

    Any `Fields` ultimately belonging to a `Store` will look in the container that the `Store` object is overwritten
    with during :py:meth:`Bonfig.load`.

    Attributes
    ----------
    name : str, optional
        Name of attribute that child `Fields` will look for their values in i.e. the value :py:attr:`Field.store_attr`
        is set to for children. Default is to set to name that `Store` instance is assigned to
        (using `__set_name__` behaviour).

    Examples
    --------
    >>> class Config(Bonfig):
    ...     a = Store('my store')
    ...     b = Store()
    ...
    ...     f1 = a.Field()
    ...     f2 = b.Field()
    >>> Config.a.name
    'my store'
    >>> Config.b.name
    'b'
    >>> Config.a.Field
    functools.partial(<class 'bonfig.fields.Field'>, _store=<Store: my store>)
    >>> Config.b.Section
    functools.partial(<class 'bonfig.fields.Section'>, _store=<Store: b>)
    """

    def __init__(self, _name=None):
        self._name = _name
        self.Section = functools.partial(Section, _store=self)

        self._with_owner = None

    @classmethod
    def _from_with(cls, with_owner):
        """Internal method for creating a 'proxy' of a :py:class:`Store` object for use in `with` blocks.

        """
        o = cls(with_owner.name)
        o._with_owner = with_owner
        return o

    @property
    def is_with_proxy(self):
        """Check if `self` is an original `Store` or a proxy of another from a `with` statement.

        """
        return self._with_owner is not None

    @property
    def name(self):
        """Name of store.

        For any `Fields` that ultimately belong to this store will have this value as :py:attr:`Field.store_attr`.
        """
        if self.is_with_proxy and self._with_owner.name:
            return self._with_owner.name
        return self._name

    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name

    def __getattr__(self, item):
        if item in fields.keys():
            return functools.partial(fields[item], _store=self)
        raise AttributeError(item)

    def __enter__(self):
        return self.__class__._from_with(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        if not self.is_with_proxy:
            return "<Store: {}>".format(self.name)
        else:
            return "<Store: {} (with proxy of {})".format(self._name, self._with_owner)


def str_bool(t):
    return t != 'False'


def _dict_keys_get(d, keys):
    """Recursively get values from d using `__getitem__`

    """
    d = d
    for k in keys:
        d = d[k]
    return d


def make_sub_field(name, bases, post_get=None, pre_set=None, doc=None):
    """
    Factory function for producing `Field`-like classes.

    Parameters
    ----------
    name : str
        Name of new field class
    post_get : func
        Function to apply to values just after they are fetched from the data :py:class:`Store`.
    pre_set : func
        Function to apply to values just before they are inserted into the data :py:class:`Store`.
    bases : cls
        Class for the newly created class to subclass (defaults to :py:class:`Field`).
    doc : str, optional
        docstring :)

    Returns
    -------
    cls : cls
        New `Field` subclass.

    Example
    -------
    >>> IntField = make_sub_field('IntField', int, str, Field)
    """
    if pre_set is None:
        def pre_set(v): return v
    if post_get is None:
        def post_get(v): return v
    if doc is None:
        doc = name

    cls = type(name, (bases,), {})
    cls._post_get = lambda s, v: post_get(v)
    cls._post_get.__doc__ = post_get.__doc__
    cls._pre_set = lambda s, v: pre_set(v)
    cls._pre_set.__doc__ = pre_set.__doc__

    cls.__doc__ = ("{}\n\n"
                   "See Also\n"
                   "--------\n"
                   "Field : Parent class").format(doc)

    return cls


class FieldDict(dict):
    """
    Subclass of dict for storing field classes.
    """
    def __init__(self, bases, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bases = bases
        self.add(bases)

    def add(self, field_cls):
        """
        Add a field_cls class to a field_cls dict. This method implicitly uses `field_cls.__name__` as the key.

        Parameters
        ----------
        field_cls : cls
            A `Field` subclass that you want to be added to the dict

        Returns
        -------
        field_cls : cls
            Returns the same field_cls instance back. This allows the method to be used as a class decorator!

        Examples
        --------
        >>> @fields.add
        >>> class ListField(Field):
        ...
        ...     def __init__(self, val=None, default=None, name=None, *, _store=None, _section=None, sep=', '):
        ...         super().__init__(val, default=default, name=name, _store=_store, _section=_section)
        ...         self.sep = sep
        ...
        ...         def post_get(self, val):
        ...             return val.split(self.sep)
        ...
        ...         def pre_set(self, val):
        ...             return self.sep.join(val)

        """
        self[field_cls.__name__] = field_cls
        return field_cls

    def make_quick(self, name, post_get=None, pre_set=None, doc_preamble=None):
        """
        Factory function for producing `Field` -like classes.

        Parameters
        ----------
        name : str
            Name of new class
        post_get : func, optional
            Function to apply to values just after they are fetched from the data Store.
        pre_set : func, optional
            Function to apply to values just before they are inserted into the data Store.
        bases : cls
            Class for the newly created class to subclass (defaults to :py:class:`Field`).
        doc_preamble : str, optional
            docstring to prepend to Field docstring!


        Returns
        -------
        cls : cls
            New Field subclass.

        Note
        ----
        Created classes are implicitly inserted into the FieldDict

        Examples
        --------
        >>> IntField = fields.make_quick('IntField', int, str)
        """
        cls = make_sub_field(name, self.bases, post_get, pre_set, doc_preamble)
        self.add(cls)
        return cls


class Field:
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed as well as how and where it's fetched from.

    Parameters
    ----------
    val : object, optional
        value that will be inserted into `store` upon initialisation. (Note if set to `None`, no value will be added to
        the `store` rather that a value equal to `None`.)
    default : object, optional
        Fallback value for this parameter if not found in `store`. If set to `None` then `AttributeError` will be
        raised.
    name : str, optional
        Key that is used to get value of `Field` as stored in `store`. Default behaviour is to take the name of the
        class attribute `Field` was set to (using `__set_name__`).
    _store : Store
        `store` that this `Field` belongs to/ looks into. Shouldn't really be set directly, instead use `Store.Field` to
        create `Field` instances.
    _section : Section, optional
        `section` that this `Field` belongs to. The `section` provides a set of 'pre-keys' that are looked up before
        `name` in `store` in order to fetch the `Field` 's value. Rather than setting directly, `Section.Field` should
        be used.

    Examples
    --------
    >>> class Config(Bonfig):
    ...     s = Store()
    ...
    ...     f1 = s.Field('first field')
    ...     f2 = s.Field()
    ...     f3 = s.Field(default='f3 not found')
    ...     f4 = s.Field('fourth field', name='field1')
    ...
    ...     def load(self):
    ...         self.s = {}
    >>> c = Config()
    >>> c.f1
    'first field'
    >>> c.f2
    KeyError: 'f2'
    >>> c.f3
    'f3 not found'
    >>> c.f4
    'forth field'
    >>> c.s
    {'f1': 'first field', 'field1': 'fourth field'}
    """

    def __init__(self, val=None, default=None, name=None, *, _store=None, _section=None):
        self.val = val
        self.name = name
        self.default = default

        if _store is None:
            raise ValueError("Parameter store cannot be None")

        self.store = _store

        self.section = _section

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    @property
    def store_attr(self):
        """Name of `Bonfig` instance attribute that values are looked up in.

        """
        return self.store.name

    def _get_store(self, bonfig):
        """Get `store` attribute from `bonfig`.

        """
        return getattr(bonfig, self.store_attr)

    @property
    def keys(self):
        """Keys used to look up value within `store`.

        """
        if self.section:
            return self.section.keys + [self.name]
        return [self.name]

    def _initialise(self, bonfig):
        """Initialise `Field`.

        This method is called during initialisation, and sets the value found within `store` at `self.keys` to
        `self.val`, unless `self.val` is `None`, in which case, nothing happens!

        Notes
        -----
        This process takes place just after :py:meth:`.Bonfig.load` and for each `Field`.
        As such any values set from :py:class:`Bonfig.load` are liable to be overwritten by `initialise`
        unless `self.val=None`.
        """
        if self.val is None:
            return  # skip

        dd = self._get_store(bonfig)
        dtype = dd.__class__
        d = dd
        for key in self.keys[:-1]:
            try:
                d = d[key]
            except KeyError:
                d[key] = dtype()
                d = d[key]
            except TypeError:
                raise TypeError("Store attribute {} is not subscriptable, "
                                "have you forgot to overwrite its value?".format(d))
        setattr(bonfig, self.store_attr, dd)
        self._set_value(self._get_store(bonfig), self._pre_set(self.val))

    def _get_value(self, store):
        """
        Hook to allow you to control how the value is looked up in the data Store.
        """
        try:
            return _dict_keys_get(store, self.keys)
        except KeyError as e:
            if self.default is not None:
                return self.default
            raise e

    def _set_value(self, store, value):
        _dict_keys_get(store, self.keys[:-1])[self.name] = value

    def _pre_set(self, val):
        """
        Apply function to values before they are inserted into data Store
        """
        return val

    def _post_get(self, val):
        """
        Apply function to values after they are fetched from data Store
        """
        return val

    def __get__(self, bonfig, owner):
        if bonfig is None:
            return self
        store = self._get_store(bonfig)
        return self._post_get(self._get_value(store))

    def __set__(self, bonfig, value):
        store = self._get_store(bonfig)
        self._set_value(store, self._pre_set(value))

    def __repr__(self):
        return "<{} '{}' stored in {}: val={}, default={}>".format(self.__class__.__name__,
                                                                   self.name,
                                                                   self.store_attr,
                                                                   self.val,
                                                                   self.default)


fields = FieldDict(Field)
IntField = fields.make_quick('IntField', int, str, 'Field that serialises and de-serialises fields that are integers')
FloatField = fields.make_quick('FloatField', float, str,
                               'Field that serialises and de-serialises fields that are floats')
BoolField = fields.make_quick('BoolField', str_bool, str,
                              'Field that serialises and de-serialises fields that are boolean')


@fields.add
class DatetimeField(Field):
    """
    Field that serialises and de-serialises fields that are datetime strings!

    See Also
    --------
    Field : Parent class
    """

    def __init__(self, val=None, default=None, name=None, fmt=None, *, _store=None, _section=None):
        super().__init__(val, default, name, _store=_store, _section=_section)
        if fmt is None:
            raise ValueError("fmt can't be None")
        self.fmt = fmt

    def _pre_set(self, val):
        return val.strftime(self.fmt)

    def _post_get(self, val):
        return datetime.datetime.strptime(val, self.fmt)


class Section:
    """
    Convenience class for building up multi-level `Bonfigs` s.

    Any `Field` s created from `Section.Field` implicitly have the `Field.section` attribute set to that `Section`.

    Parameters
    ----------
    name : str, optional
        name of Section. Default behaviour is to take the name of the class attribute `Section` was set to (using
        `__set_name__`).
    _supsection : Section, optional
        Section that owns this section. Rather than setting directly, this should be done by creating this `Section`
        instance using `supsection.Section`.
    _store : Store
        Store that section belongs to.

    Examples
    --------
    >>> class Config(Bonfig):
    ...     s = Store()
    ...
    ...     A = s.Section()
    ...     Af = A.Field('A - f')
    ...
    ...     B = A.Section('B within A')
    ...     Bf = B.Field('B - f')
    ...
    ...     def load(self):
    ...         self.s = {}
    >>>
    >>> c = Config()
    >>> c.A.keys
    ['sec_A']
    >>> c.B.keys
    ['A', 'B within A']
    >>> c.Af
    'A - f'
    >>> Config.Af.keys
    ['A', 'Af']
    >>> Config.Bf.keys
    ['A', 'B within A', 'Bf']
    >>> c.s
    {'A':
    {
    'Af': 'A - f',
    'B within A':
        {
        'Bf': 'B - f'
        }
    }
    }
    """

    def __init__(self, name=None, *, _supsection=None, _store=None):
        self._name = name

        self.supsection = _supsection
        if _store is None:
            raise ValueError("Store must be set for Sections.")

        self.store = _store

        self._with_owner = None

        self.Section = functools.partial(Section, _store=_store, _supsection=self)

    @classmethod
    def _from_with(cls, with_owner):
        """Internal method for creating a 'proxy' of a `Section` object for use in `with` blocks.

        """
        o = cls(name=with_owner.name,
                _store=with_owner.store,
                _supsection=with_owner.supsection)
        o._with_owner = with_owner
        return o

    @property
    def is_with_proxy(self):
        """Check if `self` is an original `Section` or a proxy of another from a `with` statement.

        """
        return self._with_owner is not None

    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name

    @property
    def name(self):
        """Name of Section.

        """
        if self._with_owner and self._with_owner.name:
            return self._with_owner.name
        return self._name

    @property
    def keys(self):
        """Keys used to look get to this section of the `store`

        """
        if self.supsection is not None:
            return self.supsection.keys + [self.name]
        else:
            return [self.name]

    def __getattr__(self, item):
        if item in fields.keys():
            return functools.partial(fields[item], _section=self, _store=self.store)
        raise AttributeError(item)

    def __enter__(self):
        return self.__class__._from_with(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        if not self.is_with_proxy:
            return "<Section: {}>".format(self.keys)
        else:
            return "<Section: {} (with proxy called {})>".format(self.keys, self._name)
