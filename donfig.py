import configparser
import itertools
import functools


class FieldDict(dict):

    def add(self, field):
        self[field.__name__] = field
        return field

    def make_quick(self, name, post_get, pre_set, bases=None):
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


class BaseConfig:
    
    data_attr = 'd'

    @staticmethod
    def make_data_attr():
        return {}
    
    def __init__(self, *args, **kwargs):
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
            field.__set__(self, field.default)


class PyConfig(BaseConfig):

    @staticmethod
    def make_data_attr():
        return configparser.ConfigParser()
        
    def write(self, name):
        return self.d.write(name)

    def read(self, name):
        self.d.read(name)


@fields.add
class Field:

    def __init__(self, path, default=''):
        if not isinstance(path, (list, tuple)):
            path = [path]

        self.path = list(path)
        self.default = default

    def _get_d_val(self, d, path):
        d = d
        for k in path:
            d = d[k]
        return d

    @property
    def name(self):
        return self.path[-1]

    def pre_set(self, val):
        return val

    def post_get(self, val):
        return val

    def __get__(self, instance, owner):
        if instance is None:
            return self
        d = getattr(instance, instance.__class__.data_attr)
        return self.post_get(self._get_d_val(d, self.path))

    def __set__(self, instance, value):
        d = getattr(instance, instance.__class__.data_attr)
        self._get_d_val(d, self.path[:-1])[self.name] = self.pre_set(value)


fields.make_quick('IntField', int, str)
fields.make_quick('FloatField', float, str)
fields.make_quick('BoolField', bool, str)


@pyfields.add
class PyField(Field):

    def __init__(self, name, section, default=''):
        if isinstance(section, PySection):
            path = (section.name, name)
            section.fields[name] = self
        elif isinstance(section, str):
            path = (section, name)
        super().__init__(path, default)

        self.section = section

    def __set__(self, instance, value):
        try:
            super().__set__(instance, value)
        except TypeError as e:
            raise TypeError("{} invalid as ConfigParser option values have to be strings".format(value))


pyfields.make_quick('PyIntField', int, str, bases=PyField)
pyfields.make_quick('PyFloatField', float, str, bases=PyField)
pyfields.make_quick('PyBoolField', bool, str, bases=PyField)


class PySection:

    def __init__(self, name):
        self.name = name
        self._fields = {}
        self.config_instance = None

    @property
    def fields(self):
        return self._fields

    def wrap_field(self, cls):

        @functools.wraps(cls)
        def wrapped_py_field(name, default=''):
            return cls(name, self, default)

        return wrapped_py_field

    def __getattr__(self, item):
        try:
            return self.wrap_field(pyfields[item])
        except KeyError:
            raise AttributeError(item)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return PySectionProxy(self.name, self.fields, instance)


class PySectionProxy:

    def __init__(self, name, fields, parent):
        self.name = name
        self.fields = fields
        self.parent = parent

    @property
    def d(self):
        return getattr(self.parent, self.parent.data_attr)[self.name]

    def __getitem__(self, key):
        return self.d[key]
