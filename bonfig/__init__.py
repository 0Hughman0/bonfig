"""
(c) Hugh Ramsden 2018

Bonfig
------
An alternative, more beautiful way to build configs!

Attributes
----------
fields : FieldDict
    A global `dict` -like object that stores all of the field classes. This dict is used to provide stores and sections
    with access to field classes, as such, add to this global dict to make custom fields available in that context. (By
    default includes `Field`, `IntField`, `FloatField` and `BoolField`.
"""

from .core import Bonfig, Store
from bonfig.fields import Field, fields, Section

__version__ = "0.2"
