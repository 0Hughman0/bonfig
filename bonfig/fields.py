import functools


class Store:

    def __init__(self, _name=None):
        self.name = _name
        self.Section = functools.partial(Section, store=self)
        self._store = None

    def __set_name__(self, owner, name):
        self.name = name

    def __getattr__(self, item):
        if item in fields.keys():
            return functools.partial(fields[item], store=self)
        raise AttributeError(item)


def str_bool(t):
    return t != 'False'


def _dict_path_get(d, path):
    d = d
    for k in path:
        d = d[k]
    return d


def make_sub_field(name: str, post_get, pre_set, bases=None):
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

    def make_quick(self, name: str, post_get, pre_set):
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


class Field:
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed.

    Parameters
    ----------
    keys : str, list, tuple
        'keys' to reach parameter within `store` (see examples) (optional - defaults to variable name assigned to)
    default :
        default value for this parameter, defaults to None

    Examples
    --------
    Using a str as keys:

    >>> class MyConfig(Bonfig):
    >>>     A = Field('a', default='aye')
    >>> c = MyConfig()
    >>> c.A
    'aye'
    >>> c.d
    {'a': 'aye'}

    Using a list/ tuple gives a more hierarchical structure:
    >>> class MyConfig(Bonfig):
    >>>     A = Field(('Alpha', 'a'), default='aye')
    >>>     B = Field(('Alpha', 'b'), default='bee')
    >>> c = MyConfig()
    >>> c.d
    {'Alpha': {'a': 'aye', 'b': 'bee'}}
    >>> c.A
    'aye'
    """

    def __init__(self, val=None, store= None, default=None, section=None, name=None):
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
        return self.store.name

    def get_store(self, bonfig):
        return getattr(bonfig, self.store_attr)

    @property
    def keys(self):
        if self.section:
            return self.section.keys + [self.name]
        return [self.name]

    def _check_lock(self, bonfig):
        if bonfig.locked:
            raise RuntimeError("Attempting to mutate a locked Bonfig")

    def initialise(self, bonfig):
        if self.val is None:
            return # skip

        dd = self.get_store(bonfig)
        dtype = dd.__class__
        d = dd
        for key in self.keys[:-1]:
            try:
                d = d[key]
            except KeyError:
                d[key] = dtype()
                d = d[key]
        setattr(bonfig, self.store_attr, dd)
        self._set_value(self.get_store(bonfig), self.pre_set(self.val))

    def _get_value(self, d):
        """
        Hook to allow you to control how the value is looked up in the data Store.
        """
        try:
            return _dict_path_get(d, self.keys)
        except KeyError as e:
            if self.default is not None:
                return self.default
            raise e

    def _set_value(self, store, value):
        _dict_path_get(store, self.keys[:-1])[self.name] = value

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
        store = self.get_store(bonfig)
        return self.post_get(self._get_value(store))

    def __set__(self, bonfig, value):
        self._check_lock(bonfig)
        store = self.get_store(bonfig)
        self._set_value(store, self.pre_set(value))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.store_attr)


fields = FieldDict(Field)
IntField = fields.make_quick('IntField', int, str)
FloatField = fields.make_quick('FloatField', float, str)
BoolField = fields.make_quick('BoolField', str_bool, str)


class Section:

    field_types = fields

    def __init__(self, supsection=None, name=None, store=None):
        """
        Convenience class for building up multi-level `Fields`s. Corresponds to 'sections' in `configparser.ConfigParser`
        objects.

        Parameters
        ----------
        name : str
            name of supsection

        Examples
        --------
        CSections make building up these configs a bit nicer:

        >>> class MyConfig(Bonfig):
        >>>     output = Section('Output')
        >>>     A = output.Field('a', default='foo')
        >>>     B = output.Field('b', default='bar')
        >>> c = MyConfig()
        >>> c.d
        {'Output': {'a': 'foo', 'b': 'bar'}}
        >>> c.output # is this to ugly?/ pointless?
        <Section ['Output']: {'a': <Field: ['Output', 'a']>, 'b': <Field: ['Output', 'b']>}>

        All `INIfields` are available as attributes of the INISection instance, and the `supsection` parameter will implicitly be
        set.
            """
        if isinstance(store, str):
            store = Store(store)
        elif store is None:
            raise ValueError("Store must be set for Sections.")

        self.store = store

        self.name = name

        if isinstance(supsection, str):
            supsection = [supsection]

        if isinstance(supsection, (list, tuple)):
            if len(supsection) == 1:
                supsection = Section(store=store, supsection=None, name=supsection[0])
            else:
                supsection = Section(store=store, supsection=supsection[:-1], name=supsection[-1])

        self.supsection = supsection

        self.SubSection = functools.partial(Section, store=store, supsection=self)

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    @property
    def keys(self):
        if self.supsection is not None:
            return self.supsection.keys + [self.name]
        else:
            return [self.name]

    @property
    def store_attr(self):
        return self.store.name

    def __getattr__(self, item):
        if item in fields.keys():
            return functools.partial(fields[item], section=self, store=self.store)
        raise AttributeError(item)
