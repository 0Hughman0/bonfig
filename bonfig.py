"""
(c) Hugh Ramsden 2018

Bonfig
------
An alternative, more beautiful way to build configs!

Attributes
----------
fields : FieldDict
    A dict like object that stores all of the field classes. This dict is used to provide sections with access to field
    classes, as such, add to this global dict to make custom fields available in that context.
INIfields: FieldDict
    A dict like object that stores all of the cfield classes. This dict is used to provide sections with access to
    field classes, as such, add to this global dict to make custom fields available in that context.
    
# Todo:
* make the data attr be set by the Field, rather than the Bonfig class, that way, we can store different types of data 
in the same objects, in different places, and access them seemlessly! e.g. PyField and Field in same obj, with one 
looking into a `ConfigParser` attr, and one into a `dict` attr! - I really like that 😍
"""

import configparser
import itertools
import os
import sys
import operator
import collections

from abc import abstractmethod

__version__ = "2.0"


def check_version(major, minor=0, micro=0, comp='ge'):
    return all([getattr(operator, comp)(v, v_req) for v_req, v in zip((major, minor, micro), sys.version_info)])


def make_sub_field(name, post_get, pre_set, bases=None):
    """
    Factory function for producing `Field`-like classes.

    Parameters
    ----------
    name : str
        Name of new field class
    post_get : func
        Function to apply to values just after they are fetched from the `Bonfig` data attr (usually `d`)
    pre_set : func
        Function to apply to values just before they are inserted into the `Bonfig` data attr (usually `d`)
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

    if bases is None:
        bases = Field
    cls = type(name, (bases,), {})
    cls.post_get = lambda s, v: post_get(v)
    cls.pre_set = lambda s, v: pre_set(v)
    return cls


class FieldDict(dict):
    """
    Subclass of dict for storing field classes.
    """

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

    def make_quick(self, name, post_get, pre_set, bases=None):
        """
        Factory function for producing `Field`-like classes.

        Parameters
        ----------
        name : str
            Name of new field class
        post_get : func
            Function to apply to values just after they are fetched from the `Bonfig` data attr (usually `d`)
        pre_set : func
            Function to apply to values just before they are inserted into the `Bonfig` data attr (usually `d`)
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
        cls = make_sub_field(name, post_get, pre_set, bases)
        self.add(cls)
        return cls


# Globals 😱
fields = FieldDict()
INIfields = FieldDict()



class BaseField:
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed.

    Parameters
    ----------
    path : str, list, tuple
        'path' to reach parameter within `_data_attr` (see examples) (optional - defaults to variable name assigned to)
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

    Note
    ----
    Omitting default will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff.
    """

    _data_attr = None

    @staticmethod
    @abstractmethod
    def make_data_attr():
        pass

    @abstractmethod
    def create(self, instance):
        pass

    def pre_set(self, val):
        """
        Apply function to values before they are inserted into data attr
        """
        return val

    def post_get(self, val):
        """
        Apply function to values after they are fetched from data attr
        """
        return val

    @abstractmethod
    def _get_value(self, instance):
        """
        Hook to allow you to control how the value is looked up in the underlying data structure - or not looked up
        (See EnvField!)
        """
        pass

    @abstractmethod
    def _set_value(self, instance, value):
        pass

    def _check_lock(self, instance):
        if instance.locked:
            raise RuntimeError("Attempting to mutate a locked Bonfig")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        d = getattr(instance, self._data_attr)
        return self.post_get(self._get_value(d))

    def __set__(self, instance, value):
        self._check_lock(instance)
        d = getattr(instance, self._data_attr)
        self._set_value(d, self.pre_set(value))

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self._data_attr)


class BonfigType(type):

    def __new__(mcs, name, bases, attrs, **kwargs):

        fields = collections.defaultdict(list)

        for attr in attrs.values():
            if isinstance(attr, BaseField):
                fields[attr._data_attr].append(attr)

        # Allow for inheritance
        for attr in itertools.chain(*(base.__dict__.values() for base in bases)):
            if isinstance(attr, BaseField):
                fields[attr._data_attr].append(attr)

        attrs['fields'] = fields

        return super().__new__(mcs, name, bases, attrs, **kwargs)


class Bonfig(metaclass=BonfigType):
    """
    Base class for all Bonfigs!

    Attributes
    ----------
    _data_attr : str
        name of object to store config data in, defaults to 'd'
    data attr (usually 'd') : obj
        Object used to store underlying data of `Bonfig`, (as the name of this attribute depends on _data_attr, this is
        refered to by data attr throughout documentation).

    Note
    ----
    If subclassing Bonfig and overwriting `__init__` ensure you call `super().__init__()` or the the data attr won't
    initialise properly!
    """
    
    def __init__(self, locked=False):
        self._locked = False

        for data_attr, field_list in self.fields.items():
            setattr(self, data_attr, field_list[0].make_data_attr())

            for field in field_list:
                field.create(self)

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


def _dict_path_get(d, path):
    d = d
    for k in path:
        d = d[k]
    return d


@fields.add
class Field(BaseField):
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed.

    Parameters
    ----------
    path : str, list, tuple
        'path' to reach parameter within `_data_attr` (see examples) (optional - defaults to variable name assigned to)
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

    Note
    ----
    Omitting default will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff.
    """

    _data_attr = 'd'

    @staticmethod
    def make_data_attr():
        return {}

    def __init__(self, path=None, val=None):
        if not isinstance(path, (list, tuple)) or path is None:
            path = [path]
        self.path = list(path)

        if self.name is None:
            if check_version(3, 6, comp='lt'):
                raise ValueError("name can only be left blank for Python >= 3.6")

        self.val = val

    def __set_name__(self, owner, name):
        if self.name is None:
            self.path[-1] = name

    @property
    def name(self):
        """
        Get the last item in path - i.e. the key used to fetch the parameter value from data attr
        """
        return self.path[-1]

    def create(self, instance):
        dd = instance.d
        d = dd
        for key in self.path[:-1]:
            try:
                d = d[key]
            except KeyError:
                d[key] = {}
                d = d[key]
        instance.d = dd
        self._set_value(getattr(instance, self._data_attr), self.val)

    def _get_value(self, d):
        """
        Hook to allow you to control how the value is looked up in the underlying data structure - or not looked up
        (See EnvField!)
        """
        return _dict_path_get(d, self.path)

    def _set_value(self, instance, value):
        _dict_path_get(instance, self.path[:-1])[self.name] = value


IntField = fields.make_quick('IntField', int, str)
FloatField = fields.make_quick('FloatField', float, str)
BoolField = fields.make_quick('BoolField', bool, str)


class Section:
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

    field_types = fields

    def __init__(self, path):
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

            def __init__(sself, name=None, val=None, **kwargs):
                super().__init__([*self.path, name], val, **kwargs)

        return type('Section' + cls.__name__, (WrappedPyField,), {})

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
        return _dict_path_get(getattr(self.parent, self.parent._data_attr), self.path)

    def __getitem__(self, key):
        return self.d[key]

    def __repr__(self):
        return "<Section {}: {}>".format(self.path, str(self.d))


@INIfields.add
class INIField(BaseField):
    """
    Subclass of Field whereby data is stored in a `configparser.ConfigParser` object named `parser`.

    Parameters
    ----------
    section : str
        name of section option belongs to.7
    name : str
        name of parameter option. (optional - defaults to variable name assigned to)
    default : obj
        value to default to!

    Notes
    -----
    Differs slightly from normal `Field` in that rather that taking the more general `path`, you have to provide a
    name and a section, in order to work with `ConfigParser`

    Rather than putting in the same section each time, you can make a `INISection` object...

    Omitting default will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff.
    """

    _data_attr = 'parser'

    @staticmethod
    def make_data_attr():
        return configparser.ConfigParser()

    def __init__(self, section, name=None, default=None):
        self.section = section
        self.name = name
        self.default = default

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def create(self, instance):
        parser = getattr(instance, self._data_attr)
        if self.section not in parser:
            parser[self.section] = {}
        if self.default:
            getattr(instance, self._data_attr)[self.section][self.name] = self.pre_set(self.default)

    def _get_value(self, instance):
        return getattr(instance, self._data_attr)[self.section][self.name]

    def _set_value(self, instance, value):
        getattr(instance, self._data_attr)[self.section][self.name] = value

    def __set__(self, instance, value):
        try:
            super().__set__(instance, value)
        except TypeError as e:
            raise TypeError("{} invalid as ConfigParser option values have to be strings".format(value))


INIIntField = INIfields.make_quick('INIIntField', int, str, bases=INIField)
INIFloatField = INIfields.make_quick('INIFloatField', float, str, bases=INIField)
INIBoolField = INIfields.make_quick('INIBoolField', bool, str, bases=INIField)


class INISection(Section):
    """
    Convenience class for building up `Bonfig`s. Corresponds to 'sections' in `configparser.ConfigParser` objects.

    Parameters
    ----------
    name : str
        name of section

    Examples
    --------
    CSections make building up these configs a bit nicer:

    >>> class MyConfig(Bonfig):
    >>>     output = INISection('Output')
    >>>     A = output.INIField('a', default='foo')
    >>>     B = output.INIField('b', default='bar')
    >>> c = MyConfig()
    >>> c.d
    <configparser.ConfigParser at 0x231b53f5eb8>
    >>> c.d._sections #  peer inside the config parser!
    OrderedDict([('Output', OrderedDict([('a', 'foo'), ('b', 'bar')]))])

    All `INIfields` are available as attributes of the CSection instance, and the `section` parameter will implicitly be
    set.
    """

    field_types = INIfields

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("INISections have to be at the top level for ConfigParser configurations, so name has to be"
                            "as string")
        super().__init__(name)

    def wrap_field(self, cls):
        """
        fill in section parameter as self for any class!
        """

        def wrapped_py_field(name=None, default=None, **kwargs):
            return cls(self.name, name, default, **kwargs)

        return wrapped_py_field


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

    _data_attr = 'environ'

    @staticmethod
    def make_data_attr():
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

    def create(self, instance):
        if not self.dynamic:
            self._cache = instance.environ.get(self.name, self.default)

    def _get_value(self, d):
        if not self.dynamic:
            return self._cache

        return d.get(self.name, default=self.default)


EnvIntField = make_sub_field('EnvIntField', int, str, bases=EnvField)
EnvFloatField = make_sub_field('EnvFloatField', float, str, bases=EnvField)
EnvBoolField = make_sub_field('EnvBoolField', bool, str, bases=EnvField)
