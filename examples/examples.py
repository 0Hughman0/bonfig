import datetime
from bonfig import (PyBonfig, PySection, PyField, pyfields,
                    Bonfig, Section, Field, fields)


# Using PyBonfig and PyFields/ PySections

## Creating a custom PyField
@pyfields.add
class TimePyField(PyField):

    def post_get(self, val):
        return datetime.time(int(val))

    def pre_set(self, val):
        return str(val.hour)


class PyBaseConfig(PyBonfig):

    output = PySection('Output')
    A = output.PyField('a', default='foo')
    B = output.PyField('b', default='bar')
    C = output.PyIntField('c', default=6543)

    input = PySection('Input')
    start = input.TimePyField('start-time', default=datetime.time(7))

    # or without using a PySection object:
    separate = PyField('lonely', 'Out on a limb', default='hmmm')


class Config(PyBaseConfig):

    end = PyBaseConfig.input.TimePyField('end-time', default=datetime.time(8))


c = Config()

print("\n1\n", c.d._sections, "\n")

# Reading and writing

## Writing
with open('out.ini', 'w') as f:
    c.write(f)

# Reading
print("Old value", c.start)
c.read('in.ini')
print("New value", c.start)


# Without using ConfigParser internally:

## Creating a custom PyField
@fields.add
class TimeField(Field):

    def post_get(self, val):
        return datetime.time(int(val))

    def pre_set(self, val):
        return str(val.hour)


class BaseConfig(Bonfig):

    output = Section('Output')
    A = output.Field('a', default='foo')
    B = output.Field('b', default='bar')
    C = output.IntField('c', default=6543)

    input = Section('Input')
    start = input.TimeField('start-time', default=datetime.time(7))

    # or without using a PySection object:
    separate = Field(('Out on a limb', 'lonely'), default='hmmm')

    # More levels possible when using regular Bonfig:
    multi = Field(('one', 'two', 'three', 'four'), default='FOUR LEVELS IN!')


class Config(BaseConfig):

    end = BaseConfig.input.TimeField('end-time', default=datetime.time(8))


c = Config()

print("\n2\n", c.d, "\n")


# Making a nice chill config:

class ChillConfig(Bonfig):

    A = Field('a')
    B = Field('b')
    C = Field('c')


c = ChillConfig()
print("\n\n3")
print(c.d)
print(c.A)
c.A = 'Cats!'
print(c.A)
print(c.d)


