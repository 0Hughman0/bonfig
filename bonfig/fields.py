import functools


class Store:
    """
    Class for storing data of `Fields` owned by this store.

    Examples
    --------
    >>> # Todo
    """

    def __init__(self, _name=None):
        self._name = _name
        self.Section = functools.partial(Section, store=self)

        self._with_owner = None

    @classmethod
    def _from_with(cls, with_owner):
        """Internal method for creating a 'proxy' of a `Store` object for use in `with` blocks.

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

        For any `Fields` that ultimately belong to this store will have this value as `Field.store_attr`.
        """
        if self.is_with_proxy and self._with_owner.name:
            return self._with_owner.name
        return self._name

    def __set_name__(self, owner, name):
        if self._name is None:
            self._name = name

    def __getattr__(self, item):
        if item in fields.keys():
            return functools.partial(fields[item], store=self)
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


def make_sub_field(name, post_get, pre_set, bases):
    """
    Factory function for producing `Field`-like classes.

    Parameters
    ----------
    name : str
        Name of new field class
    post_get : func
        Function to apply to values just after they are fetched from the data `Store`.
    pre_set : func
        Function to apply to values just before they are inserted into the data `Store`.
    bases : cls
        Class for the newly created class to subclass (defaults to `Field`).

    Returns
    -------
    cls : cls
        New `Field` subclass.

    Example
    -------
    >>> IntField = make_sub_field('IntField', int, str)
    """
    cls = type(name, (bases,), {})
    cls.post_get = lambda s, v: post_get(v)
    cls.post_get.__doc__ = post_get.__doc__
    cls.pre_set = lambda s, v: pre_set(v)
    cls.pre_set.__doc__ = pre_set.__doc__
    return cls


class FieldDict(dict):
    """
    Subclass of dict for storing field classes.
    """
    def __init__(self, bases, *args,**kwargs):
        super().__init__(*args, **kwargs)
        self.bases = bases
        self.add(bases)

    def add(self, field_cls):
        """
        Add a field_cls class to a field_cls dict. This method implicitly uses `field_cls.__name__` as the key.

        Example
        -------
        >>> # Todo

        Parameters
        ----------
        field_cls : cls
            A `Field` subclass that you want to be added to the dict

        Returns
        -------
        field_cls : cls
            Returns the same field_cls instance back. This allows the method to be used as a class decorator!
        """
        self[field_cls.__name__] = field_cls
        return field_cls

    def make_quick(self, name, post_get, pre_set):
        """
        Factory function for producing `Field` -like classes.

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
    store : Store, str
        `store` that this `Field` belongs to/ looks into. Shouldn't really be set directly, instead use `Store.Field` to
        create `Field` instances, as this will implicitly set the correct `store` value. If provided as a `str`, this
        will simply be turned into a `Store` object of the same name... so you might as well use the suggested route!
    section : Section, optional
        `section` that this `Field` belongs to. The `section` provides a set of 'pre-keys' that are looked up before
        `name` in `store` in order to fetch the `Field` 's value. Rather than setting directly, `Section.Field` should
        be used.

    Examples
    --------
    >>> # Todo
    """

    def __init__(self, val=None, default=None, name=None, *, store=None, section=None):
        self.val = val
        self.name = name

        if isinstance(store, str):
            store = Store(store)
        if store is None:
            raise ValueError("Parameter store cannot be None")

        self.store = store

        self.default = default

        if section is not None and not isinstance(section, Section):
            raise ValueError("Section must be None, or an instance of Section")
        self.section = section

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

    def _check_lock(self, bonfig):
        if bonfig.locked:
            raise RuntimeError("Attempting to mutate a locked Bonfig")

    def initialise(self, bonfig):
        """Initialise `Field`.

        This method is called during initialisation, and sets the value found within `store` at `self.keys` to
        `self.val`, unless `self.val` is `None`, in which case, nothing happens!

        Notes
        -----
        This process takes place just after `Bonfig.load` and for each `Field` is finished before `Bonfig.finalise`.
        As such any values set from `Bonfig.load` are liable to be overwritten by `initialise` unless `self.val=None`,
        and in turn those values can be overwritten by `Bonfig.finalise` - but hopefully that's not unexpected!
        """
        if self.val is None:
            return # skip

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
                raise ValueError("Store attribute {} is not subscriptable, have you forgot to overwrite its value?".format(d))
        setattr(bonfig, self.store_attr, dd)
        self._set_value(self._get_store(bonfig), self.pre_set(self.val))

    def _get_value(self, d):
        """
        Hook to allow you to control how the value is looked up in the data Store.
        """
        try:
            return _dict_keys_get(d, self.keys)
        except KeyError as e:
            if self.default is not None:
                return self.default
            raise e

    def _set_value(self, store, value):
        _dict_keys_get(store, self.keys[:-1])[self.name] = value

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

    def __get__(self, bonfig, owner):
        if bonfig is None:
            return self
        store = self._get_store(bonfig)
        return self.post_get(self._get_value(store))

    def __set__(self, bonfig, value):
        self._check_lock(bonfig)
        store = self._get_store(bonfig)
        self._set_value(store, self.pre_set(value))

    def __repr__(self):
        return "<{} stored in {}: val={}, default={}>".format(self.__class__.__name__,
                                                              self.store_attr,
                                                              self.val,
                                                              self.default)


fields = FieldDict(Field)
IntField = fields.make_quick('IntField', int, str)
FloatField = fields.make_quick('FloatField', float, str)
BoolField = fields.make_quick('BoolField', str_bool, str)


class Section:

    field_types = fields

    def __init__(self, name=None, *, supsection=None, store=None):
        """
        Convenience class for building up multi-level `Bonfigs` s.

        Any `Field` s created from `Section.Field` implicitly have the `Field.section` attribute set to that `Section`.

        Parameters
        ----------
        name : str, optional
            name of Section. Default behaviour is to take the name of the class attribute `Section` was set to (using
            `__set_name__`).
        supsection : Section, optional
            Section that owns this section. Rather than setting directly, this should be done by creating this `Section`
            instance using `supsection.Section`.
        store : Store

        Examples
        --------
        >>> # Todo
        """
        if isinstance(store, str):
            store = Store(store)
        elif store is None:
            raise ValueError("Store must be set for Sections.")

        self.store = store

        self._name = name

        if isinstance(supsection, str):
            supsection = [supsection]

        if isinstance(supsection, (list, tuple)):
            if len(supsection) == 1:
                supsection = Section(store=store, supsection=None, name=supsection[0])
            else:
                supsection = Section(store=store, supsection=supsection[:-1], name=supsection[-1])

        self.supsection = supsection

        self.SubSection = functools.partial(Section, store=store, supsection=self)

        self._with_owner = None

    @classmethod
    def _from_with(cls, with_owner):
        """Internal method for creating a 'proxy' of a `Section` object for use in `with` blocks.

        """
        o = cls(supsection=with_owner.supsection,
                name=with_owner.name,
                store=with_owner.store)
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
            return functools.partial(fields[item], section=self, store=self.store)
        raise AttributeError(item)

    def __enter__(self):
        return self.__class__._from_with(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __repr__(self):
        if not self.is_with_proxy:
            return "<Section: {}>".format(self.keys)
        else:
            return "<Section: {} (with proxy)".format(self.keys)
