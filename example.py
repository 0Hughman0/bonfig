import datetime
from donfig import PyConfig, PySection, BaseConfig, Field, PyField, pyfields


@pyfields.add
class TimePyField(PyField):

    def post_get(self, val):
        return datetime.time(int(val))

    def pre_set(self, val):
        return str(val.hour)


class PyBaseConfig(PyConfig):

    output = PySection('Output')

    A = output.PyField('a', default='foo')
    B = output.PyField('b', default='bar')
    C = output.PyIntField('c', default=6543)

    input = PySection('Input')
    start = input.TimePyField('start-time', default=datetime.time(7))


class Config(PyBaseConfig):

    end = PyBaseConfig.input.TimePyField('end-time', default=datetime.time(8))


c = Config()
c.input.fields


class OtherConfig(BaseConfig):

    level1 = Field('Title')

c2 = OtherConfig()