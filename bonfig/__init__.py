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
Create an abstract base class for the data attribute that very loosely wraps the data storage class, e.g. the dict,
ConfigParser or Environment. This allows for consistent read write syntax (can add a JSON class in that case).

This also means we can make the initialisation work like:

    >>> c = MyBonfig()
    ...     .parser.read('mine.ini')
    ...     .json.read('ting.json')

Which I think is a nice compromise.
"""

__version__ = "2.0"

from .core import Bonfig
