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
pyfields: FieldDict
    A dict like object that stores all of the pyfield classes. This dict is used to provide sections with access to
    field classes, as such, add to this global dict to make custom fields available in that context.
"""

import configparser
import itertools
import functools
import os
import sys
import operator

__version__ = "0.2"


def _check_version(major, minor=0, micro=0, comp='ge'):
    return all([getattr(operator, comp)(v, v_req) for v_req, v in zip((major, minor, micro), sys.version_info)])


class FieldDict(dict):
    """
    Subclass of dict for storing field classes.
    """

    def add(self, field):
        """
        Add a field class to a field dict. This method implicitly uses `field.__name__` as the key.

        Example
        -------
        >>> from bonfig import pyfields
        >>> @pyfields.add
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
            Function to apply to values just after they are fetched from the `Bonfig` `data_attr` (usually `d`)
        pre_set : func
            Function to apply to values just before they are inserted into the `Bonfig` `data_attr` (usually `d`)
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
        if bases is None:
            bases = Field
        cls = type(name, (bases,), {})
        cls.post_get = lambda s, v: post_get(v)
        cls.pre_set = lambda s, v: pre_set(v)
        self.add(cls)
        return cls


# Globals 😱
fields = FieldDict()
pyfields = FieldDict()


class Bonfig:
    """
    Base class for all Bonfigs!

    Attributes
    ----------
    data_attr : str
        name of class to store config data in, defaults to 'd'

    Note
    ----
    If subclassing Bonfig and overwriting `__init__` ensure you call `super().__init__()` or the the `data_attr` won't
    initialise properly!
    """
    
    data_attr = 'd'

    @staticmethod
    def make_data_attr():
        """
        Hook to allow using a different type for `data_attr`.

        Returns
        -------
        mapping : obj
            some dict-like class.

        Note
        ----
        To change the data attribute, overwrite this method
        """
        return {}
    
    def __init__(self):
        cls = self.__class__

        fields = [attr for attr in 
                  itertools.chain(*(kls.__dict__.values() for kls in (cls, *cls.__bases__)))
                  if isinstance(attr, Field)] # Allow inheritance!
            
        d = cls.make_data_attr()
        setattr(self, cls.data_attr, d)
        
        # Intialise internal dict structure!
        for field in fields:
            dd = d
            for key in field.path[:-1]:
                try:
                    dd = dd[key]
                except KeyError:
                    dd[key] = {}
                    dd = dd[key]
            if field.default is not None:
                field.__set__(self, field.default)


class PyBonfig(Bonfig):
    """
    Subclass of `Bonfig` which utilizes a `configparser.ConfigParser` as the data_attr

    Parameters
    ----------
    filenames : str, path, bytes
        file to load values from on initialisation. Defaults to None, in which case, no loading takes place...
        obviously?
    """

    def __init__(self, filenames=None):
        super().__init__()
        if filenames:
            self.read(filenames)

    @staticmethod
    def make_data_attr():
        return configparser.ConfigParser()
        
    def write(self, f, *args, **kwargs):
        """
        Write config to file using `ConfigPaser.write`

        Parameters
        ----------
        f : file-like
            file-like object to write to
        *args
            additional parameters to pass to `write`
        **kwargs
            additional parameters to pass to `write`
        """
        self.d.write(f, *args, **kwargs)

    def read(self, filenames, *args, **kwargs):
        """
        Read config from file using `ConfigPaser.read`

        Parameters
        ----------
        name : str
            name of file to write to
        *args
            additional parameters to pass to `read`
        **kwargs
            additional parameters to pass to `read`
        """
        self.d.read(filenames)


def _dict_path_get(d, path):
    d = d
    for k in path:
        d = d[k]
    return d


@fields.add
class Field:
    """
    Class representing a parameter from your configuration. This object encapsulates how this parameter is serialised
    and deserialsed.

    Parameters
    ----------
    path : str, list, tuple
        'path' to reach parameter within `data_attr` (see examples)
    default :
        default value for this parameter

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
    Setting default to None will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff. As such most of the time you
    want it to be set to '' (the default).
    """

    def __init__(self, path=None, default=''):
        if not isinstance(path, (list, tuple)) or path is None:
            path = [path]
        self.path = list(path)

        if self.name is None:
            if _check_version(3, 6, comp='lt'):
                raise TypeError("name can only be left blank for Python >= 3.6")

        self.default = default

    def __set_name__(self, owner, name):
        if self.name is None:
            self.path[-1] = name

    @property
    def name(self):
        """
        Get the last item in path - i.e. the key used to fetch the parameter value from `data_attr`
        """
        return self.path[-1]

    def pre_set(self, val):
        """
        Apply function to values before they are inserted into `data_attr`
        """
        return val

    def post_get(self, val):
        """
        Apply function to values after they are fetched from `data_attr`
        """
        return val

    def _get_value(self, d, path):
        """
        Hook to allow you to control how the value is looked up in the underlying data structure - or not looked up
        (See EnvField!)
        """
        return _dict_path_get(d, path)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        d = getattr(instance, instance.__class__.data_attr)
        return self.post_get(self._get_value(d, self.path))

    def __set__(self, instance, value):
        d = getattr(instance, instance.__class__.data_attr)
        self._get_value(d, self.path[:-1])[self.name] = self.pre_set(value)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.path)


IntField = fields.make_quick('IntField', int, str)
FloatField = fields.make_quick('FloatField', float, str)
BoolField = fields.make_quick('BoolField', bool, str)


class Section:
    """
    Convenience class for building up `PyBonfig`s. Corresponds to 'sections' in `configparser.ConfigParser` objects.

    Parameters
    ----------
    name : str
        name of section

    Examples
    --------
    PySections make building up these configs a bit nicer:

    >>> class MyConfig(Bonfig):
    >>>     output = Section('Output')
    >>>     A = output.Field('a', default='foo')
    >>>     B = output.Field('b', default='bar')
    >>> c = MyConfig()
    >>> c.d
    {'Output': {'a': 'foo', 'b': 'bar'}}
    >>> c.output # is this to ugly?/ pointless?
    <Section ['Output']: {'a': <Field: ['Output', 'a']>, 'b': <Field: ['Output', 'b']>}>

    All `pyfields` are available as attributes of the PySection instance, and the `section` parameter will implicitly be
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
        @functools.wraps(cls)
        def wrapped_py_field(name=None, default='', **kwargs):
            return cls([*self.path, name], default, **kwargs)

        return wrapped_py_field

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
        return _dict_path_get(getattr(self.parent, self.parent.data_attr), self.path)

    def __getitem__(self, key):
        return self.d[key]

    def __repr__(self):
        return "<Section {}: {}>".format(self.path, str(self.d))


@pyfields.add
class PyField(Field):
    """
    Subclass of field, specifically for use with `PyBonfig` - i.e. for use with `configparser.ConfigParser` as the
    `data_attr`.

    Parameters
    ----------
    name : str
        name of parameter option.
    section : str
        name of section option belongs to.7
    default : obj
        value to default to!

    Notes
    -----
    Differs slightly from normal `Field` in that rather that taking the more general `path`, you have to provide a
    name and a section, in order to work with `ConfigParser`

    Rather than putting in the same section each time, you can make a `PySection` object...

    Setting default to None will result in no values being entered in the data attr upon initialisation, which might
    make the structure of the data attr look a bit weird until you fill it up with stuff. As such most of the time you
    want it to be set to '' (the default).
    """

    def __init__(self, section, name=None, default=''):
        if isinstance(section, PySection):
            path = [section.name, name]
        else:
            path = [section, name]
        super().__init__(path, default)

        self.section = section

    def __set__(self, instance, value):
        try:
            super().__set__(instance, value)
        except TypeError as e:
            raise TypeError("{} invalid as ConfigParser option values have to be strings".format(value))


PyIntField = pyfields.make_quick('PyIntField', int, str, bases=PyField)
PyFloatField = pyfields.make_quick('PyFloatField', float, str, bases=PyField)
PyBoolField = pyfields.make_quick('PyBoolField', bool, str, bases=PyField)


class PySection(Section):
    """
    Convenience class for building up `PyBonfig`s. Corresponds to 'sections' in `configparser.ConfigParser` objects.

    Parameters
    ----------
    name : str
        name of section

    Examples
    --------
    PySections make building up these configs a bit nicer:

    >>> class MyConfig(PyBonfig):
    >>>     output = PySection('Output')
    >>>     A = output.PyField('a', default='foo')
    >>>     B = output.PyField('b', default='bar')
    >>> c = MyConfig()
    >>> c.d
    <configparser.ConfigParser at 0x231b53f5eb8>
    >>> c.d._sections #  peer inside the config parser!
    OrderedDict([('Output', OrderedDict([('a', 'foo'), ('b', 'bar')]))])

    All `pyfields` are available as attributes of the PySection instance, and the `section` parameter will implicitly be
    set.
    """

    field_types = pyfields

    def __init__(self, name):
        if not isinstance(name, str):
            raise TypeError("PySections have to be at the top level for ConfigParser configurations, so name has to be"
                            "as string")
        super().__init__(name)

    def wrap_field(self, cls):
        """
        fill in section parameter as self for any class!
        """

        @functools.wraps(cls)
        def wrapped_py_field(name=None, default='', **kwargs):
            return cls(self, name, default, **kwargs)

        return wrapped_py_field


class EnvField(Field):
    """
    A config Field where it's value is looked up in your environment variables.

    Parameters
    ----------
    name : str
        name of environment variable to look up
    default : str
        fallback value if not found

    Notes
    -----
    Environment variables can also be set with this Field type.

    As the value is looked up every time, and is not stored in the data attr, for example when using PyBonfig, it's
    value won't be written to disk.
    """

    def __init__(self, name=None, default=''):
        if not isinstance(name, str) and name is not None:
            raise TypeError("Environment variable name must be a string!")

        super().__init__(name, None)

        self.env_default = default

    def _get_value(self, d, path):
        if not path:
            return os.environ
        return os.environ.get(self.name, default=self.env_default)
