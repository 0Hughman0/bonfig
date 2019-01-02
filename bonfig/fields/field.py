from bonfig.fields.base import BaseField, FieldDict, str_bool


def _dict_path_get(d, path):
    d = d
    for k in path:
        d = d[k]
    return d


class Field(BaseField):
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed.

    Parameters
    ----------
    path : str, list, tuple
        'path' to reach parameter within `_store_attr` (see examples) (optional - defaults to variable name assigned to)
    default :
        default value for this parameter, defaults to None

    Examples
    --------
    Using a str as path:

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

    _store_attr = 'd'

    def __init__(self, val, path=None):
        self.val = val

        if not isinstance(path, (list, tuple)) or path is None:
            path = [path]
        self.path = list(path)

    def __set_name__(self, owner, name):
        if self.name is None:
            self.path[-1] = name

    @property
    def name(self):
        """
        Get the last item in path - i.e. the key used to fetch the parameter value from data Store
        """
        return self.path[-1]

    def initialise(self, bonfig):
        dd = self.get_store(bonfig)
        dtype = dd.__class__
        d = dd
        for key in self.path[:-1]:
            try:
                d = d[key]
            except KeyError:
                d[key] = dtype()
                d = d[key]
        setattr(bonfig.stores, self._store_attr, dd)
        self._set_value(self.get_store(bonfig), self.pre_set(self.val))

    def _get_value(self, d):
        """
        Hook to allow you to control how the value is looked up in the data Store.
        """
        return _dict_path_get(d, self.path)

    def _set_value(self, store, value):
        _dict_path_get(store, self.path[:-1])[self.name] = value


fields = FieldDict(Field)
IntField = fields.make_quick('IntField', int, str)
FloatField = fields.make_quick('FloatField', float, str)
BoolField = fields.make_quick('BoolField', str_bool, str)


class Section:

    field_types = fields

    def __init__(self, path):
        """
        Convenience class for building up multi-level `Fields`s. Corresponds to 'sections' in `configparser.ConfigParser`
        objects.

        Parameters
        ----------
        name : str
            name of section

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

        All `INIfields` are available as attributes of the INISection instance, and the `section` parameter will implicitly be
        set.
            """
        if not isinstance(path, (list, tuple)) or path is None:
            path = [path]
        self.path = list(path)

    @property
    def name(self):
        return self.path[-1]

    def wrap_field(self, cls):
        """
        fill in section parameter as self for any class!
        """
        class WrappedPyField(cls):

            def __init__(sself, val, name=None, **kwargs):
                path = self.path + [name]
                super().__init__(val, path, **kwargs)

        return type(cls.__name__ + 'Section', (WrappedPyField,), {})

    def __getattr__(self, item):
        try:
            return self.wrap_field(self.field_types[item])
        except KeyError:
            raise AttributeError(item)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return SectionProxy(self.path, instance)


class SectionProxy:

    def __init__(self, path, parent):
        self.path = path
        self.parent = parent

    @property
    def name(self):
        return self.parent.name

    @property
    def d(self):
        return _dict_path_get(getattr(self.parent.bstores, self.parent._store_attr), self.path)

    def __getitem__(self, key):
        return self.d[key]

    def __repr__(self):
        return "<Section {}: {}>".format(self.path, str(self.d))
