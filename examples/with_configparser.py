import datetime
import sys
from pathlib import Path
sys.path.append(Path().parent)

from bonfig import (PyBonfig, INISection, INIField, INIfields)

"""
Using PyBonfig and PyFields/ PySections
=======================================
"""


class BasicConfig(PyBonfig):

    output = INISection('Output')
    A = output.PyField('A Really Long Descriptive Name', default='foo')
    B = output.PyField(default='bar')
    C = output.PyIntField('c')

    # or without using a PySection object:
    separate = INIField('lonely', 'Out on a limb', default='hmmm')


"""
    >>> c = BasicConfig()
    >>> c.d
    <configparser.ConfigParser at 0x22a0df724a8>
    >>> c.d._sections # Reveals internals of ConfigParser
    OrderedDict([('Output',
              OrderedDict([('a really long descriptive name', 'foo'),
                           ('b', 'bar')])),
             ('lonely', OrderedDict([('out on a limb', 'hmmm')]))])
    >>> c.C = 1353
    >>> c.C
    1353
    >>> c.d._sections
    OrderedDict([('Output',
              OrderedDict([('a really long descriptive name', 'foo'),
                           ('b', 'bar'),
                           ('c', '153')])),
             ('lonely', OrderedDict([('out on a limb', 'hmmm')]))])
"""

"""
Loading and writing to a .ini file
==================================
"""

"""
    >>> with open('examples/out.ini', 'w') as f:
    ...     c.write(f)
    >>> ("Old value", c.A)
    ('Old value', 'foo')
    >>> c.read('examples/in.ini')
    >>> ("New value", c.A)
    ('New value', 365)
    
# or just load on initialisation:

    >>> c = Config('examples/out.ini')
    >>>> ("Back to Old", c.A)
    ('Back to Old', 'foo')
"""

"""
Writing a custom PyField
========================
"""


# Creating a custom PyField
@INIfields.add
class TimePyField(INIField):

    def post_get(self, val):
        return datetime.time(int(val))

    def pre_set(self, val):
        return str(val.hour)


class CustomConfig(BasicConfig):

    times = INISection('Times')
    start = times.TimePyField('start-time')
    end_time = times.TimePyField(default=datetime.time(8))


"""
    >>> c = CustomConfig()
    >>> c.d._sections
    OrderedDict([('Times', OrderedDict([('end_time', '8')])),
             ('Output',
              OrderedDict([('a really long descriptive name', 'foo'),
                           ('b', 'bar')])),
             ('lonely', OrderedDict([('out on a limb', 'hmmm')]))])
    >>> c.start = datetime.time(10)
    >>> c.d._sections
    OrderedDict([('Times', OrderedDict([('end_time', '8'), ('start-time', '10')])),
             ('Output',
              OrderedDict([('a really long descriptive name', 'foo'),
                           ('b', 'bar')])),
             ('lonely', OrderedDict([('out on a limb', 'hmmm')]))])
    >>> c.end_time
    datetime.time(8, 0)
"""
