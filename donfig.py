import datetime
import configparser
import itertools

null = lambda o: o


class BaseConfig:
    
    data_attr = 'd'
    
    def __new__(cls, *args, **kwargs):
        o = super().__new__(cls, *args, **kwargs)
        
        fields = [attr for attr in 
                    itertools.chain(*(kls.__dict__.values() for kls in (cls, *cls.__bases__)))
                        if isinstance(attr, Field)] # Allow inheritance!
            
        d = {}
        setattr(o, cls.data_attr, d)
        
        # Intialise internal dict structure!
        for field in fields:
            print(d)
            dd = d
            for key in field.path[:-1]:
                try:
                    dd = dd[key]
                except KeyError:
                    dd[key] = {}
                    dd = dd[key]
            field.__set__(o, field.default)
        
        return o
        

class PyConfig(BaseConfig):
    
    def make_configparser(self):
        return configparser.ConfigParser()
        
    def to_configparser(self):
        p = self.make_configparser()
        p.read_dict(self.d)
        return p
        
    def write(self, name):
        p = self.to_configparser()
        with open(name, 'w') as f:
            p.write(f)
        return p
    
    def read_file(self, name):
        with open(name) as f:
            p = self.make_configparser()
            p.read_file(f)
            
        self.d = p._sections
        

class Section:

    def __init__(self, name):
        self.name = name
        
    def field(self, path, default=''):
        if not isinstance(path, (list, tuple)):
            path = [path]
        
        return Field(path.insert(0, self.name), default)
        
        
class Field:

    def __init__(self, path, default=''):
        if not isinstance(path, (list, tuple)):
            path = [path]
        
        self.path = path    

        self.default = default
        self._postget = None
        self._preset = None
        
        self._prewrite = None
        self._postread = None
        
    def _get_d_val(self, o, path):
        d = getattr(o, o.__class__.data_attr)
        for k in path:
            d = d[k]
        return d
    
    @property
    def name(self):
        return self.path[-1]
    
    def preset(self, f):
        self._preset = f
        return self
        
    def postget(self, f):
        self._postget = f
        return self
    
    def __get__(self, instance, owner):
        if self._postget:
            return self._postget(self._get_d_val(instance, self.path))
        return self._get_d_val(instance, self.path)
        
    def __set__(self, instance, value):
        if self._preset:
            value = self._preset(value)
        self._get_d_val(instance, self.path[:-1])[self.name] = value




