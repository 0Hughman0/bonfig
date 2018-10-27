import datetime
from donfig import PyConfig, Field
import configparser

class BaseConfig_(PyConfig):

    A = Field(('Output', 'a'), default='foo')
    B = Field(('Output', 'b'), default='bar')
    
    start = Field(('Input', 'start-time'), default=datetime.time(7))
    
    @start.postget
    def f(B):        
        return datetime.time(int(B))
        
    @start.preset
    def f(time):
        return time.hour


class Config(BaseConfig_):

    end = Field(('Input', 'end-time'), default=datetime.time(8))
        
c = Config()
"""
>>> c.A
''
>>> c.end
datetime.time(8, 0)
>>> c.d
{'Input': {'end-time': datetime.time(8, 0), 'start-time': 7}, 'Output': {'a': '', 'b': ''}}
>>> c.end = datetime.time(3)
>>> c.d
{'Input': {'end-time': datetime.time(3, 0), 'start-time': 7}, 'Output': {'a': '', 'b': ''}}
>>> c.write('t.ini')
>>> p = configparser()
>>> p.read_file(open('t.ini'))
>>> p.sections()
['Output', 'Input']
>>> c.to_configparser() == p
True
"""
